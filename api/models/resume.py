from sqlalchemy import Column, Integer, String, ForeignKey,Text, DateTime, TIMESTAMP,JSON
from database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey('companies.id'))
    user_id = Column(Integer, ForeignKey('users.user_id'))
    job_title =Column(String(255))
    candidate_email=Column(String(255))
    file_path = Column(String(255))
    resume_extract_data=Column(JSON)
    result = Column(JSON) 
    uploaded_at = Column(DateTime, default=func.now())

    user = relationship("AI_Interviewer", back_populates="resume")
    company = relationship("Companies", back_populates="resume")
    resume_analysis = relationship("Resume_Analysis", back_populates="resume")
    question = relationship("Question", back_populates="resume")
    



   