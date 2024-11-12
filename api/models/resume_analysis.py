from sqlalchemy import Column, Integer, String, ForeignKey,Text, DateTime, TIMESTAMP,JSON
from database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class Resume_Analysis(Base):
    __tablename__ = "resume_analysis4"

    id = Column(Integer, primary_key=True, autoincrement=True)
    resume_id = Column(Integer, ForeignKey('resumes.id'))
    hr_id = Column(Integer, ForeignKey('users.user_id'))
    job_title = Column(Text)
    candidate_name=Column(String(250))
    candidate_email=Column(String(250))
    candidate_phone=Column(String(250))
    overall_score =Column(String(250))
    relevance_score = Column(String(250))
    experience_match_score =Column(String(250))
    cultural_fit_score = Column(String(250))
    resume_selection_status=Column(String(250))
    strengths=Column(JSON)
    weaknesses=Column(JSON)
    recommendations=Column(JSON)
    missing_elements=Column(JSON)
    uploaded_at = Column(DateTime, default=func.now())

    resume = relationship("Resume", back_populates="resume_analysis")

    user = relationship("AI_Interviewer", back_populates="resume_analysis")

    
    
   