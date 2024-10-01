from sqlalchemy import Column, Integer, String, ForeignKey,Text, DateTime, TIMESTAMP
from database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class InterviewReport(Base):
    __tablename__ = "interview_report"

    id = Column(Integer, primary_key=True, autoincrement=True)
    interview_id = Column(Integer, ForeignKey('interviews.id'))
    report_content = Column(Text)
    status = Column(String(100))
    created_on = Column(DateTime, default=func.now())

    interviews = relationship("Interview", back_populates="interview_report")

    