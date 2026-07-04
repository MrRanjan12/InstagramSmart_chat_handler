from sqlalchemy.orm import Session

from backend.models.message import Message


class MessageService:

    def save_user_message(
        self,
        db: Session,
        conversation_id: int,
        text: str,
    ):

        message = Message(
            conversation_id=conversation_id,
            role="user",
            content=text
        )

        db.add(message)
        db.commit()
        db.refresh(message)

        return message

    def save_ai_message(
            self,
            db: Session,
            conversation_id: int,
            text: str
    ):
        message = Message(
            conversation_id = conversation_id,
            role = "assistant",
            content = text
        )

        db.add(message)
        db.commit()
        db.refresh(message)

        return message
    
message_service = MessageService()