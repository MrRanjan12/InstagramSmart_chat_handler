from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from backend.config import config
from backend.constants import ASTRA, RANJAN
from backend.models.user import User
from backend.models.conversation import Conversation
from backend.models.message import Message
from backend.services.assistant_router import AssistantRouter
from backend.services.memory_service import memory_service
from backend.services.message_service import message_service
from backend.services.escalation.engine import IntentEngine
from backend.instagram import instagram_api


class EscalationService:
    def __init__(self, engine: Optional[IntentEngine] = None):
        self.engine = engine or IntentEngine()

    def _should_auto_reset(self, db: Session, conversation_id: int) -> bool:
        """
        Checks if the conversation has been inactive for longer than
        ESCALATION_AUTO_RESET_HOURS. If so, automatically reverts to AI mode.
        """
        auto_reset_hours = getattr(config, "ESCALATION_AUTO_RESET_HOURS", 12)
        if auto_reset_hours <= 0:
            return False

        # Fetch the two most recent messages
        # (index 0 is the current message just saved, index 1 is the previous message before the silence)
        recent_messages = (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(2)
            .all()
        )

        if not recent_messages:
            return False

        # Use the previous message if available, otherwise the single message
        reference_message = recent_messages[1] if len(recent_messages) > 1 else recent_messages[0]

        if not reference_message.created_at:
            return False

        now = datetime.now(timezone.utc)
        ref_time = reference_message.created_at
        if ref_time.tzinfo is None:
            ref_time = ref_time.replace(tzinfo=timezone.utc)

        elapsed = now - ref_time
        return elapsed >= timedelta(hours=auto_reset_hours)

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

        # Step 2: Check current state - if in Human mode (RANJAN)
        if AssistantRouter.is_human_mode(user):
            # Check if inactivity timeout has elapsed -> AUTO-RESET to ASTRA
            if self._should_auto_reset(db, conversation_id):
                print(
                    f"[ESCALATION] Inactivity timeout reached for user {user.Instagram_id}. "
                    f"Automatically switching mode from RANJAN to ASTRA (AI)."
                )
                AssistantRouter.switch_mode(user, ASTRA)
                db.commit()
                db.refresh(user)
                # Fall through to Step 3 so the AI immediately handles this new message!
            else:
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
