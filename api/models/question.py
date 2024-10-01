from sqlalchemy import Column, Integer, String, ForeignKey,Text, DateTime, TIMESTAMP,JSON, Boolean
from database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

class Question(Base):
    __tablename__ = "question"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column (Text)
    is_ai_generated  = Column(Boolean, server_default='0', nullable=False)
    created_on = Column(DateTime, default=func.now())
    updated_on = Column(TIMESTAMP, server_default=func.now(), onupdate=func.current_timestamp())