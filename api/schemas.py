from pydantic import BaseModel,  Field, EmailStr, validator
from typing import Optional, List
from fastapi import UploadFile, File
from datetime import date, datetime
from enum import Enum
from sqlalchemy import JSON
import re


######################################## User logiin and register #############################
class LoginInput(BaseModel):
    email: str
    user_password: str


class ChangePassword(BaseModel):
    current_password: str
    new_password: str

    class Config:
        from_attributes = True


class UserType(str, Enum):
    admin = "admin"
    HR = "HR"
    user = "user"
    Students="students"
   


class UserCreate(BaseModel):
    user_name: str
    user_email: str
    user_password: str
    user_type: UserType = UserType.user
    phone_no: str
    company_name: Optional[str] = None
    industry:  Optional[str] = None

    class Config:
        from_attributes = True


class UpdateUser(BaseModel):
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    phone_no: Optional[int] = None
    user_type: Optional[str] = None
    current_password: Optional[str] = None

########################### for interview_report ###########################

class Interview_StatusType(str, Enum):
    Scheduled = "Scheduled"
    Completed = "Completed"
    Pending = "Pending"
    Rescheduled = "Rescheduled"
    In_progress = "in_progress"

########################### for interviews  ###########################
class Interviews_Type(str, Enum):
    Technical = "Technical"
    Behavioral = "Behavioral"
    Initial_Screening = "Initial_Screening"

################################ company #####################

class CompanyCreate(BaseModel):
    company_name: str
    industry: str
    hr_id: int
    company_address: Optional[str] = None
    contact_info: Optional[str] = None

class CompanyUpdate(BaseModel):
    company_name: Optional[str] = None
    industry: Optional[str] = None
    company_address: Optional[str] = None
    contact_info: Optional[str] = None

################################## Resume ######################

class ResumeCreate(BaseModel):
    user_id: int
    file_path: str
    status: Optional[str] = "pending"
    screened_at: Optional[datetime] = None

class ResumeUpdate(BaseModel):
    status: Optional[str] = None
    screened_at: Optional[datetime] = None

########################### Job discription #####################

class JDCreate(BaseModel):
    job_title: str
    job_description: str
    requirements: str
    location: Optional[str] = None
    company_id: int

class JDUpdate(BaseModel):
    job_title: Optional[str] = None
    job_description: Optional[str] = None
    requirements: Optional[str] = None
    location: Optional[str] = None
    
################################ interview ########################
class InterviewCreate(BaseModel):
    job_description_id: int
    resume_id: int
    company_id: int
    interview_date: datetime
    interview_type: Optional[str] = None
    status: Optional[str] = "scheduled"

class InterviewUpdate(BaseModel):
    interview_date: Optional[datetime] = None
    interview_type: Optional[str] = None
    status: Optional[str] = None

################################ Business Message ########################

class CompanyBase(BaseModel):
    company_name: str
    contact_person_name: str
    business_email: str
    phone_number: str | None = None
    company_website: str | None = None
    company_size: str
    company_description: str

class CompanyCreate(CompanyBase):
    pass

######################################## job posting in table model ##########################

class JobStatus(str, Enum):
    DRAFT = "Draft"
    PUBLISHED = "Published"

# Enum for Job Type
class JobType(str, Enum):
    FULL_TIME = "Full-time"
    PART_TIME = "Part-time"
    CONTRACT = "Contract"
    INTERNSHIP = "Internship"

class Employmenttype(str, Enum):
    Remote ="Remote"
    On_site="On_site"
    Hybrid="Hybrid"

# Pydantic model for job posting creation
class JobPostingCreate(BaseModel):
    job_title: Optional[str]
    job_description: Optional[str]
    company_name: Optional[str]
    department: Optional[str]
    location: Optional[str]
    job_type: Optional[JobType]
    experience_required: Optional[str]
    employment_type: Optional[Employmenttype]
    requirements: Optional[str]
    responsibilities: Optional[str]
    salary_range: Optional[str]
    benefits: Optional[str]
    application_deadline: Optional[date]
    status: Optional[JobStatus]


    


   