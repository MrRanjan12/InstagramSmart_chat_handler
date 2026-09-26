from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.config import config
from backend.constants import ASTRA, RANJAN
from backend.models.user import User
from backend.models.conversation import Conversation
from backend.services.assistant_router import AssistantRouter
from backend.services.memory_service import memory_service
from backend.services.message_service import message_service
from backend.services.escalation.engine import IntentEngine
from backend.instagram import instagram_api


class EscalationService:
    def __init__(self, engine: Optional[IntentEngine] = None):
        self.engine = engine or IntentEngine()

    def evaluate_and_route(
        self,
        db: Session,
        user: User,
        conversation_id: int,
        current_message: str
    ) -> Dict[str, Any]:
        """
        Evaluates incoming message and conversation state.
        Determines whether AI should reply or if human escalation is triggered.
        """
        # Step 1: Check if escalation is globally disabled
        if not getattr(config, "ESCALATION_ENABLED", True):
            return {
                "should_ai_reply": True,
                "current_mode": user.current_node,
                "was_escalated": False,
                "reason": "escalation_disabled"
            }

        # Step 2: Check current state - if already in Human mode (RANJAN), block AI
        if AssistantRouter.is_human_mode(user):
            print(f"[ESCALATION] User {user.Instagram_id} is in HUMAN (RANJAN) mode. Skipping AI reply.")
            return {
                "should_ai_reply": False,
                "current_mode": RANJAN,
                "was_escalated": False,
                "reason": "human_mode_active"
            }

        # Step 3: AI mode (ASTRA) - Run Intent Engine analysis
        recent_messages = memory_service.get_recent_messages(
            db=db,
            conversation_id=conversation_id,
            limit=5
        )

        # Collect recent user messages for context
        user_texts = [m.content for m in recent_messages if m.role == "user"]
        if current_message and (not user_texts or user_texts[-1] != current_message):
            user_texts.append(current_message)

        if not user_texts and current_message:
            user_texts = [current_message]

        intent_result = self.engine.analyze(user_texts)

        threshold = getattr(config, "ESCALATION_THRESHOLD", 80)
        should_escalate = (
            intent_result.intent_score >= threshold
            or intent_result.human_request_detected
        )

        print(
            f"[ESCALATION] Intent Score: {intent_result.intent_score} | "
            f"Classification: {intent_result.intent_classification} | "
            f"Escalate: {should_escalate}"
        )

        # Step 4: Handle Escalation Transition (ASTRA -> RANJAN)
        if should_escalate:
            print(f"[ESCALATION] Switching user {user.Instagram_id} from ASTRA to RANJAN (Human takeover).")
            AssistantRouter.switch_mode(user, RANJAN)
            db.commit()
            db.refresh(user)

            handoff_sent = False
            silent_mode = getattr(config, "ESCALATION_SILENT", False)
            handoff_msg = getattr(
                config,
                "ESCALATION_HANDOFF_MESSAGE",
                "Haan bhai ek second, main thoda busy tha, abhi free hoke reply karta hu."
            )

            if not silent_mode and handoff_msg:
                try:
                    message_service.save_ai_message(db, conversation_id, handoff_msg)
                    instagram_api.send_message(user.Instagram_id, handoff_msg)
                    handoff_sent = True
                    print(f"[ESCALATION] Sent persona handoff message: '{handoff_msg}'")
                except Exception as e:
                    print(f"[ESCALATION] Error sending handoff message: {e}")

            return {
                "should_ai_reply": False,
                "current_mode": RANJAN,
                "was_escalated": True,
                "handoff_sent": handoff_sent,
                "intent_result": intent_result,
                "reason": "escalated_to_human"
            }

        # Step 5: Normal AI handling
        return {
            "should_ai_reply": True,
            "current_mode": ASTRA,
            "was_escalated": False,
            "intent_result": intent_result,
            "reason": "ai_handling"
        }

    def switch_user_mode(self, db: Session, instagram_id: str, new_mode: str) -> Optional[User]:
        """
        Manually switch a user between ASTRA and RANJAN.
        """
        if new_mode not in (ASTRA, RANJAN):
            raise ValueError(f"Invalid mode: {new_mode}. Must be {ASTRA} or {RANJAN}.")

        user = db.query(User).filter(User.Instagram_id == instagram_id).first()
        if not user:
            return None

        AssistantRouter.switch_mode(user, new_mode)
        db.commit()
        db.refresh(user)
        return user

    def reset_to_ai(self, db: Session, instagram_id: str) -> Optional[User]:
        """
        Resets conversation mode back to AI (ASTRA).
        """
        return self.switch_user_mode(db, instagram_id, ASTRA)

    def get_user_status(self, db: Session, instagram_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves current mode and conversation state for an Instagram user.
        """
        user = db.query(User).filter(User.Instagram_id == instagram_id).first()
        if not user:
            return None

        conversation = db.query(Conversation).filter(Conversation.user_id == user.id).first()

        return {
            "user_id": user.id,
            "instagram_id": user.Instagram_id,
            "current_mode": user.current_node,
            "is_human_active": AssistantRouter.is_human_mode(user),
            "conversation_id": conversation.id if conversation else None
        }


escalation_service = EscalationService()
