from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import ForeignKey
from sqlalchemy import DateTime
from sqlalchemy import Text

from datetime import datetime, timezone

from backend.database import Base


class Message(Base):
    __tablename__ = "message"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id"),
        nullable=False
    )

    role = Column(
        String,
        nullable=False
    )

    content = Column(
        Text,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )