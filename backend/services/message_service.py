from sqlalchemy.orm import Session

from backend.models.message import Message


class MessageService:

    @staticmethod
    def save(
        db: Session,
        conversation_id: int,
        sender: str,
        message: str
    ):

        msg = Message(
            conversation_id=conversation_id,
            sender=sender,
            message=message
        )

        db.add(msg)
        db.commit()
        db.refresh(msg)

        return msg

    @staticmethod
    def history(
        db: Session,
        conversation_id: int,
        limit: int = 20
    ):

        return (
            db.query(Message)
            .filter(
                Message.conversation_id == conversation_id
            )
            .order_by(
                Message.id.desc()
            )
            .limit(limit)
            .all()
        )