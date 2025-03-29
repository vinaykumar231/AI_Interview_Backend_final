from sqlalchemy import Column, Integer, String, ForeignKey,Text, DateTime, TIMESTAMP,JSON
from database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class S_Video(Base):
    __tablename__ = "s_videos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_path = Column(String(255))
    uploaded_at = Column(DateTime, default=func.now())

    



   