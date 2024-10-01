from sqlalchemy import Column, Integer, String, ForeignKey,Text, DateTime, TIMESTAMP,JSON, Boolean
from database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_name= Column(Integer, ForeignKey('companies.id'))
    job_description_id = Column(Integer, ForeignKey('job_descriptions_tb.id'))
    interviewer_hr_id = Column(Integer, ForeignKey('users.user_id'))
    candidate_id = Column(Integer, ForeignKey('users.user_id'))
    scheduled_time= Column (DateTime)
    duration = Column(Integer) 
    interview_type = Column(String(50)) 
    interview_status = Column(String(100))
    created_at = Column(DateTime, default=func.now())

    interviewer_user = relationship("AI_Interviewer", foreign_keys=[interviewer_hr_id], back_populates="interviews_as_interviewer")
    
    company = relationship("Companies", back_populates="Interview")

    interviewee_user = relationship("AI_Interviewer", foreign_keys=[candidate_id ], back_populates="interviews_as_interviewee")
    
    interview_report = relationship("InterviewReport", back_populates="interviews")

    

    

