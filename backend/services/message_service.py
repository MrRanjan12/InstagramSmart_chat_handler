from sqlalchemy.orm import Session
from backend.models.message import Message


class MessageService:

    def save_user_message(
        self,
        db: Session,
        conversation_id: int,
        text: str,
    ):
        safe_content = str(text) if text is not None and str(text).strip() != "" else "[Empty or non-text message]"

        message = Message(
            conversation_id=conversation_id,
            role="user",
            content=safe_content
        )

        try:
            db.add(message)
            db.commit()
            db.refresh(message)
            return message
        except Exception:
            db.rollback()
            raise

    def save_ai_message(
        self,
        db: Session,
        conversation_id: int,
        text: str
    ):
        safe_content = str(text) if text is not None else ""

        message = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=safe_content
        )

        try:
            db.add(message)
            db.commit()
            db.refresh(message)
            return message
        except Exception:
            db.rollback()
            raise


message_service = MessageService()