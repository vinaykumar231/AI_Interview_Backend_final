from fastapi import HTTPException, Depends
from database import Base
from sqlalchemy.sql import func
from sqlalchemy import Column, String, Integer, Boolean, DateTime, TIMESTAMP, BIGINT, Enum, ForeignKey
from datetime import datetime
import re
from sqlalchemy.orm import relationship,session
from ..schemas import LoginInput,UserCreate
from database import api_response, get_db, SessionLocal
from datetime import datetime
import re
from sqlalchemy.orm import relationship
import bcrypt
from api.schemas import ChangePassword, LoginInput, UpdateUser, UserType
from auth.auth_handler import signJWT
import pytz
from ..models.company import Companies


class AI_Interviewer(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(String(255))
    user_email = Column(String(255), unique=True)
    user_password = Column(String(255))
    company_name= Column(String(250), default=None)
    industry= Column(String(250),default=None)
    user_type = Column(String(100))
    phone_no = Column(BIGINT)
    created_on = Column(DateTime, default=func.now())
    updated_on = Column(TIMESTAMP, server_default=func.now(), onupdate=func.current_timestamp())
   
    resume = relationship("Resume", back_populates="user")

    interviews_as_interviewer = relationship("Interview", foreign_keys='Interview.interviewer_hr_id', back_populates="interviewer_user")

    interviews_as_interviewee = relationship("Interview", foreign_keys='Interview.candidate_id ', back_populates="interviewee_user")
    
    company = relationship("Companies", back_populates="user")

    job_descriptions = relationship("Job_Descriptions", back_populates="user")

    s_resumes_upload = relationship("Resume_upload", back_populates="user")

    resume_analysis = relationship("Resume_Analysis", back_populates="user")

    # #######################################################################################################################
    @staticmethod
    def validate_email(email):
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(email_pattern, email)

    @staticmethod
    def validate_password(password):
        return len(password) >= 8

    @staticmethod
    def validate_phone_number(phone_number):
        phone_pattern = r"^\d{10}$"
        return re.match(phone_pattern, phone_number)
    
   
    @staticmethod
    def AI_Interviewers_login(credential: LoginInput):
        try:
            session = SessionLocal()
            user = session.query(AI_Interviewer).filter(AI_Interviewer.user_email == credential.email).first()

            if not user:
                return HTTPException(500, detail=f"Record with Email : {credential.email} not found")

            if bcrypt.checkpw(credential.user_password.encode('utf-8'), user.user_password.encode('utf-8')):
                token, exp = signJWT(user.user_id, user.user_type)
                if user.user_type == "HR" or user.user_type == "admin":
                    response = {
                            'token': token,
                            'exp' : exp,
                            'user_id': user.user_id,
                            'user_name': user.user_name,
                            'user_email': user.user_email,
                            'user_type': user.user_type,
                            'created_on': user.created_on,
                            'phone_no': user.phone_no,
                            'company_name': user.company_name,
                            'industry': user.industry,
                            
                        }
                else:
                    response = {
                        'token': token,
                        'exp' : exp,
                        'user_id': user.user_id,
                        'user_name': user.user_name,
                        'user_email': user.user_email,
                        'user_type': user.user_type,
                        'created_on': user.created_on,
                        'phone_no': user.phone_no,
                           
                    }

                return response
            else:
                return HTTPException(500, detail='Invalid email or password')

        except Exception as e:
            return HTTPException(status_code=500, detail=f"Error: {str(e)}")

    