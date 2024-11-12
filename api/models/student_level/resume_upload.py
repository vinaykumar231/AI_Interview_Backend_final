from sqlalchemy import Column, Integer, String, ForeignKey,Text, DateTime, TIMESTAMP,JSON
from database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class Resume_upload(Base):
    __tablename__ = "resumes_upload"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    file_path = Column(String(255))
    resume_extract_data=Column(JSON)
    result = Column(JSON) 
    uploaded_at = Column(DateTime, default=func.now())

    user = relationship("AI_Interviewer", back_populates="s_resumes_upload")
    s_resume_analysis = relationship("S_Resume_Analysis", back_populates="s_resumes_upload")
    question = relationship("S_Question", back_populates="resume")
    
    



   