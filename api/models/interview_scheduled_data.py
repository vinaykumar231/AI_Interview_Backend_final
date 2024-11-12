from sqlalchemy import Column, Integer, String, ForeignKey, Date, Time, DateTime, JSON, Boolean
from database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

class InterviewScheduledData(Base):
    __tablename__ = "interview_scheduled"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_name = Column(String(250), nullable=False)
    candidate_email = Column(String(250), nullable=False)
    interview_date = Column(Date, nullable=False)  
    interview_time = Column(Time, nullable=False)   
    created_on = Column(DateTime, default=func.now())
    updated_on = Column(DateTime, onupdate=func.now())  
