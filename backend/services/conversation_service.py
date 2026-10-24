from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.models.user import User
from backend.models.conversation import Conversation


class ConversationService:

    def get_or_create_user(self, db: Session, instagram_id: str):
        user = (
            db.query(User)
            .filter(User.Instagram_id == str(instagram_id))
            .first()
        )

        if user:
            return user

        user = User(
            Instagram_id=str(instagram_id)
        )

        try:
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        except IntegrityError:
            db.rollback()
            return (
                db.query(User)
                .filter(User.Instagram_id == str(instagram_id))
                .first()
            )

    def get_or_create_conversation(self, db: Session, user_id: int):
        conversation = (
            db.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(Conversation.id.desc())
            .first()
        )

        if conversation:
            return conversation

        conversation = Conversation(
            user_id=user_id
        )

        try:
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            return conversation
        except IntegrityError:
            db.rollback()
            return (
                db.query(Conversation)
                .filter(Conversation.user_id == user_id)
                .order_by(Conversation.id.desc())
                .first()
            )


conversation_service = ConversationService()