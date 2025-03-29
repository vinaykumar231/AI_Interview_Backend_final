from sqlalchemy import Column, Integer, String, ForeignKey,Text, DateTime, TIMESTAMP,JSON
from database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class S_Resume_Analysis(Base):
    __tablename__ = "s_resume_analysis2"

    id = Column(Integer, primary_key=True, autoincrement=True)
    resume_id = Column(Integer, ForeignKey('resumes_upload.id'))
    job_title = Column(Text)
    resume_score = Column(Integer)  # Change to Integer
    resume_recommendations=Column(JSON)
    resume_missing_elements=Column(JSON)
    candidate_name=Column(String(250))
    candidate_email=Column(String(250))
    candidate_phone=Column(String(250))
    strengths=Column(JSON)
    weaknesses=Column(JSON)
    overall_score = Column(Integer)  # Change to Integer
    overall_suggestion = Column(JSON)  # Change to JSON if it's a list
    uploaded_at = Column(DateTime, default=func.now())

    s_resumes_upload = relationship("Resume_upload", back_populates="s_resume_analysis")
   
   