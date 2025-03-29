from sqlalchemy import Column, Integer, String, ForeignKey,Text, DateTime, TIMESTAMP,JSON, Boolean
from database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

class S_Question(Base):
    __tablename__ = "s_question1"

    id = Column(Integer, primary_key=True, autoincrement=True)
    resume_id = Column(Integer, ForeignKey('resumes_upload.id'))
    candidate_name=Column(String(250))
    candidate_email=Column(String(250))
    Qustion1 = Column (Text)
    Qustion2 = Column (Text)
    Qustion3 = Column (Text)
    Qustion4 = Column (Text)
    Qustion5 = Column (Text)
    is_ai_generated  = Column(Boolean, server_default='0', nullable=False)
    created_on = Column(DateTime, default=func.now())
    updated_on = Column(TIMESTAMP, server_default=func.now(), onupdate=func.current_timestamp())

    resume = relationship("Resume_upload", back_populates="question")
    
    
def generate_gemini_prompt_Question(job_description: str) -> str:
     # Create the prompt for the Gemini API
        prompt = f"""
        You are tasked with preparing a set of basic interview questions for the following job role, but question should be profesional that can be answered within 30 to 60 seconds.
        Please generate 15 relevant interview questions based on the job description, with 5 questions from each of the following categories:

        1. Experience-Based Questions
        2. Behavioral Questions
        3. Cultural Fit and Career Development Questions

        Job Description: {job_description}

        Please structure the response in valid JSON format with the following keys:
        
        experience_based_questions: A list of 5 relevant experience-based questions,
        behavioral_questions: A list of 5 relevant behavioral questions,
        cultural_fit_and_career_development_questions: A list of 5 relevant cultural fit and career development questions
        
        """
        return prompt