from sqlalchemy import Column, Date, Enum, Integer, String, ForeignKey,Text, DateTime, TIMESTAMP,JSON, Boolean
from database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..schemas import JobStatus, JobType, Employmenttype


class JobPostingTable(Base):
    __tablename__ = "job_postings_tb1"
    id = Column(Integer, primary_key=True, index=True)
    hr_id = Column(Integer, ForeignKey('users.user_id'))
    job_title = Column(String(100),  nullable=True)
    job_description = Column(Text,  nullable=True)
    company_name = Column(String(255), nullable=True)
    department = Column(String(100),  nullable=True)
    location = Column(String(100),  nullable=True)
    job_type = Column(Enum(JobType),  nullable=True)          #Full-time Part-time Contract Internship
    experience_required = Column(String(50),  nullable=True)
    employment_type =  Column(Enum(Employmenttype), nullable=True)  # Remote, On-site, Hybrid  
    requirements = Column(Text, nullable=True)
    responsibilities = Column(Text, nullable=True)
    salary_range = Column(String(50), nullable=True)
    benefits = Column(Text, nullable=True)
    application_deadline = Column(Date,  nullable=True)
    status = Column(Enum(JobStatus), nullable=True) #"Draft PUBLISHED  "Closed"
    is_published = Column(Boolean, server_default='0', nullable=False)
    created_on = Column(DateTime, default=func.now())
    updated_on = Column(TIMESTAMP, server_default=func.now(), onupdate=func.current_timestamp())

    user = relationship("AI_Interviewer", back_populates="job_posting")
   