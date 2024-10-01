from sqlalchemy import Column, Integer, String, ForeignKey,Text, DateTime, TIMESTAMP
from database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

class Job_Descriptions(Base):
    __tablename__ = "job_descriptions_tb"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey('companies.id'))
    user_id = Column(Integer, ForeignKey('users.user_id'))
    job_title = Column(Text)
    job_description = Column(Text)
    #requirements = Column(Text)
    created_on = Column(DateTime, default=func.now())
    updated_on = Column(TIMESTAMP, server_default=func.now(), onupdate=func.current_timestamp())

    company = relationship("Companies", back_populates="job_descriptions")

    user = relationship("AI_Interviewer", back_populates="job_descriptions")

    

    