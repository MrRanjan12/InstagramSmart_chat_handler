from sqlalchemy.orm import Session

from backend.models.conversation import Conversation


class ConversationService:

    @staticmethod
    def create(
        db: Session,
        user_id: int
    ):

        conversation = Conversation(
            user_id=user_id
        )

        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        return conversation

    @staticmethod
    def latest(
        db: Session,
        user_id: int
    ):

        return (
            db.query(Conversation)
            .filter(
                Conversation.user_id == user_id
            )
            .order_by(
                Conversation.id.desc()
            )
            .first()
        )