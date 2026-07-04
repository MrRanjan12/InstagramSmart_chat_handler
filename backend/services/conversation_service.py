from sqlalchemy.orm import Session

from backend.models.user import User
from backend.models.conversation import Conversation


class ConversationService:

    def get_or_create_user(self, db: Session, instagram_id: str):

        user = (
            db.query(User)
            .filter(User.Instagram_id == instagram_id)
            .first()
        )

        if user:
            return user

        user = User(
            Instagram_id=instagram_id
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    def get_or_create_conversation(self, db: Session, user_id: int):

        conversation = (
            db.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .first()
        )

        if conversation:
            return conversation

        conversation = Conversation(
            user_id=user_id
        )

        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        return conversation


conversation_service = ConversationService()