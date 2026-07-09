from sqlalchemy.orm import Session
from backend.models.message import Message


class MemoryService:
    def get_recent_messages(self, db: Session, conversation_id: int, limit: int = 20):
        messages = (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
            .all()
        )

        # DB se latest-first aata hai, AI ko chronological (oldest-first) chahiye
        return list(reversed(messages))


memory_service = MemoryService()