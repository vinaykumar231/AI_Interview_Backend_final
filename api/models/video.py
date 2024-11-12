from sqlalchemy import Column, Integer, String, ForeignKey,Text, DateTime, TIMESTAMP,JSON
from database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_email=Column(String(250))
    hr_id = Column(Integer)
    file_path = Column(String(255))
    uploaded_at = Column(DateTime, default=func.now())

    



   