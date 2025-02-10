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

################################################### job apply #############################

class JobDetailSchema(BaseModel):
    job_title: Optional[str] = None
    company_name:Optional[str] = None
    job_duration_from: Optional[date] = None
    job_duration_to: Optional[date] = None
    job_skills: Optional[str] = None
    job_summary: Optional[str] = None

    @validator("job_duration_from", "job_duration_to", pre=True)
    def validate_date(cls, value):
        return None if value == "" else value

class EducationSchema(BaseModel):
    degree: str
    field_of_study: str
    institution_name: str
    year_of_passing: int

class ProjectSchema(BaseModel):
    project_name: Optional[str] = None
    description: Optional[str] = None
    technologies_used:  Optional[str] = None

class CertificationSchema(BaseModel):
    certification_name: Optional[str] = None
    issued_by:  Optional[str] = None
    issued_date:  Optional[str] = None

class CandidateProfileSchema(BaseModel):
    gender: str
    date_of_birth: str
    country: str
    province_state: str
    city: str
    job_domain_function:  Optional[str] = None
    job_sub_role: Optional[str] = None
    experience: Optional[float] = None
    total_experience_years: Optional[int] = None
    #total_experience_months: int
    current_company_name: Optional[str] = None
    current_job_title: Optional[str] = None
    joining_date:Optional[date] = None
    current_ctc: Optional[float] = None
    expected_ctc: Optional[float] = None
    job_profile:  Optional[str] = None
    notice_period:  Optional[str] = None
    educations: list[EducationSchema]
    projects: list[ProjectSchema]
    certifications: list[CertificationSchema]
    job_details: List[JobDetailSchema]

    @validator("experience", "current_ctc", "expected_ctc", pre=True)
    def validate_float(cls, value):
        return None if value == "" else value

    @validator("joining_date", "date_of_birth", pre=True)
    def validate_date_fields(cls, value):
        return None if value == "" else value

    class Config:
        orm_mode = True


    


   