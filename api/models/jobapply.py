from sqlalchemy import Boolean, Column, Integer, String, Date, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base

class CandidateProfile(Base):
    __tablename__ = "candidate_profiles_tb"

    candidate_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False) 

    # Personal Details
    gender = Column(String(255), nullable=False)  
    date_of_birth = Column(Date, nullable=False)
    country = Column(String(255), nullable=False)
    province_state = Column(String(255), nullable=False)
    city = Column(String(255), nullable=False)

    # Industry
    job_domain_function = Column(String(255), nullable=False)
    job_sub_role = Column(String(255), nullable=False)
    experience = Column(Float, nullable=False)

    # Employment
    total_experience_years = Column(Integer, nullable=False)
    total_experience_months = Column(Integer, nullable=False)
    current_company_name = Column(String(255), nullable=False)
    current_job_title = Column(String(255), nullable=False)
    joining_date = Column(Date, nullable=False)
    current_ctc = Column(Float, nullable=False)
    expected_ctc = Column(Float, nullable=False)
    job_profile = Column(String(255), nullable=True)
    notice_period = Column(String(255), nullable=True)

    is_job_applied  = Column(Boolean, server_default='0', nullable=False)

    # Relationships
    educations = relationship("Education", back_populates="candidate_profile", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="candidate_profile", cascade="all, delete-orphan")
    certifications = relationship("Certification", back_populates="candidate_profile", cascade="all, delete-orphan")
    job_details = relationship("JobDetail", back_populates="candidate_profile", cascade="all, delete-orphan")
    user = relationship("AI_Interviewer", back_populates="candidate_profile")

class Education(Base):
    __tablename__ = "educations_tb"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidate_profiles_tb.candidate_id"), nullable=False)  
    degree = Column(String(255), nullable=False)  
    field_of_study = Column(String(255), nullable=False)  
    institution_name = Column(String(255), nullable=False)  
    year_of_passing = Column(Integer, nullable=False) 

    candidate_profile = relationship("CandidateProfile", back_populates="educations")

class Project(Base):
    __tablename__ = "projects_tb"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidate_profiles_tb.candidate_id"), nullable=False)  
    project_name = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)
    technologies_used = Column(String(255), nullable=True)

    candidate_profile = relationship("CandidateProfile", back_populates="projects")

class Certification(Base):
    __tablename__ = "certifications_tb"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidate_profiles_tb.candidate_id"))  
    certification_name = Column(String(255), nullable=False)
    issued_by = Column(String(255), nullable=False)
    issued_date = Column(Date, nullable=False)

    candidate_profile = relationship("CandidateProfile", back_populates="certifications")

class JobDetail(Base):
    __tablename__ = "job_details_tb"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidate_profiles_tb.candidate_id"), nullable=False)  
    job_title = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=False)
    job_duration_from = Column(Date, nullable=False)  
    job_duration_to = Column(Date, nullable=True)  
    job_skills = Column(Text, nullable=True)  
    job_summary = Column(Text, nullable=True)  

    candidate_profile = relationship("CandidateProfile", back_populates="job_details")
