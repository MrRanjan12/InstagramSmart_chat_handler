from sqlalchemy import Column, DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.sql import func

from backend.database import Base

class User(Base):
    
    __tablename__= "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    Instagram_id = Column(
        String,
        unique=True,
        nullable=False
    )

    current_node = Column(
        String,
        default="ASTRA"
    )

    created_at = Column(

        DateTime,
        server_default=func.now()
    )