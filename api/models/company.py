from sqlalchemy import Column, Integer, String, ForeignKey,Text, DateTime, TIMESTAMP,JSON, Boolean
from database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

class Companies(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_name= Column(String(250))
    industry= Column(String(250))
    hr_id=Column(Integer, ForeignKey('users.user_id'))
    created_on = Column(DateTime, default=func.now())

    Interview = relationship("Interview", back_populates="company")

    user = relationship("AI_Interviewer", back_populates="company")

    job_descriptions = relationship("Job_Descriptions", back_populates="company")

    resume = relationship("Resume", back_populates="company")
   
