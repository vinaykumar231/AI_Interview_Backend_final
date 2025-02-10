from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from api.models.jobapply import CandidateProfile, Certification, Education, Project, JobDetail
from api.models.user import AI_Interviewer
from auth.auth_bearer import get_current_user
from database import get_db
from ..schemas import CandidateProfileSchema
import logging
from sqlalchemy.orm import joinedload

router = APIRouter()

@router.post("/candidate_profiles", response_model=None)
def create_candidate_profile(
    profile_data: CandidateProfileSchema,
    db: Session = Depends(get_db),
    current_user: AI_Interviewer = Depends(get_current_user)
):
    try:
        job_apply = db.query(CandidateProfile).filter(
            CandidateProfile.is_job_applied == True,
            CandidateProfile.user_id == current_user.user_id
        ).first()
        if job_apply:
            raise HTTPException(status_code=400, detail="You have already applied for a job.")

        new_profile = CandidateProfile(
            user_id=current_user.user_id,
            gender=profile_data.gender,
            date_of_birth=profile_data.date_of_birth,
            country=profile_data.country,
            province_state=profile_data.province_state,
            city=profile_data.city,
            job_domain_function=profile_data.job_domain_function,
            job_sub_role=profile_data.job_sub_role,
            experience=profile_data.experience,
            total_experience_years=profile_data.total_experience_years,
            #total_experience_months=profile_data.total_experience_months,
            current_company_name=profile_data.current_company_name,
            current_job_title=profile_data.current_job_title,
            joining_date=profile_data.joining_date,
            current_ctc=profile_data.current_ctc,
            expected_ctc=profile_data.expected_ctc,
            job_profile=profile_data.job_profile,
            notice_period=profile_data.notice_period,
        )
        db.add(new_profile)
        db.commit()
        db.refresh(new_profile)

        for edu in profile_data.educations:
            new_education = Education(
                candidate_id=new_profile.user_id,
                degree=edu.degree,
                field_of_study=edu.field_of_study,
                institution_name=edu.institution_name,
                year_of_passing=edu.year_of_passing,
            )
            db.add(new_education)

        for proj in profile_data.projects:
            new_project = Project(
                candidate_id=new_profile.user_id,
                project_name=proj.project_name,
                description=proj.description,
                technologies_used=proj.technologies_used,
            )
            db.add(new_project)

        for cert in profile_data.certifications:
            new_certification = Certification(
                candidate_id=new_profile.user_id,
                certification_name=cert.certification_name,
                issued_by=cert.issued_by,
                issued_date=cert.issued_date,
            )
            db.add(new_certification)

        for job in profile_data.job_details:
            new_job_detail = JobDetail(
                candidate_id=new_profile.user_id,
                job_title=job.job_title,
                company_name=job.company_name,
                job_duration_from=job.job_duration_from,
                job_duration_to=job.job_duration_to,
                job_skills=job.job_skills,
                job_summary=job.job_summary,
            )
            db.add(new_job_detail)

        db.commit()
        
        new_profile.is_job_applied = True

        return {"message": "job apply successfully."}
    except HTTPException as http_exc:
        raise http_exc

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail= f"A database error occurred while creating the candidate profile.{e}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred while creating the candidate profile.{e}")
    
@router.get("/candidate_profiles/{candidate_id}", response_model=None)
def get_candidate_profile(candidate_id: int, db: Session = Depends(get_db)):
    try:
        candidate_profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == candidate_id).\
            options(joinedload(CandidateProfile.user)).first()

        if not candidate_profile:
            raise HTTPException(status_code=404, detail="Candidate profile not found")

        educations = db.query(Education).filter(Education.candidate_id == candidate_profile.user_id).all()
        
        projects = db.query(Project).filter(Project.candidate_id == candidate_profile.user_id).all()

        certifications = db.query(Certification).filter(Certification.candidate_id == candidate_profile.user_id).all()

        job_details = db.query(JobDetail).filter(JobDetail.candidate_id == candidate_profile.user_id).all()

        user_name = candidate_profile.user.user_name if candidate_profile.user else None

        response_data = {
            "candidate_profile": candidate_profile,
            "user_name": user_name,
            "educations": educations,
            "projects": projects,
            "certifications": certifications,
            "job_details": job_details
        }

        if candidate_profile.user:
            del candidate_profile.user.user_password  
        if candidate_profile.user:
            del candidate_profile.user.company_name  
        if candidate_profile.user:
            del candidate_profile.user.industry 

        return response_data
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        raise HTTPException(
            status_code=500, detail="An error occurred while fetching the candidate profile."
        )

@router.get("/candidate_profiles/", response_model=None)
def get_all_candidate_profiles(db: Session = Depends(get_db)):
    try:
        candidate_profiles = db.query(CandidateProfile).all()
        
        if not candidate_profiles:
            raise HTTPException(status_code=404, detail="No candidate profiles found")

        all_data = []
        for profile in candidate_profiles:
            educations = db.query(Education).filter(Education.candidate_id == profile.user_id).all()
            projects = db.query(Project).filter(Project.candidate_id == profile.user_id).all()
            certifications = db.query(Certification).filter(Certification.candidate_id == profile.user_id).all()
            job_details = db.query(JobDetail).filter(JobDetail.candidate_id == profile.user_id).all()

            all_data.append({
                "candidate_profile": profile,
                "educations": educations,
                "projects": projects,
                "certifications": certifications,
                "job_details": job_details
            })

        return all_data
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        raise HTTPException(
            status_code=500, detail="An error occurred while fetching candidate profiles."
        )
