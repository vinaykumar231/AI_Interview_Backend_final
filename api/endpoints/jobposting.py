from fastapi import APIRouter, FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from pydantic import BaseModel
from typing import Optional
from api.models.user import AI_Interviewer
from auth.auth_bearer import JWTBearer, get_admin_or_hr, get_current_user
from database import get_db 
from ..schemas import   JobPostingCreate  
from ..models.jobposting import JobPostingTable
from sqlalchemy.orm import Session, joinedload

router = APIRouter()

@router.post("/job_postings/", response_model=None, dependencies=[Depends(JWTBearer()), Depends(get_admin_or_hr)])
def create_job_posting(job_posting: JobPostingCreate, db: Session = Depends(get_db), current_user: AI_Interviewer = Depends(get_current_user)):
    
    hr_user = db.query(AI_Interviewer).filter(AI_Interviewer.user_id == current_user.user_id).first()
    if not hr_user:
        raise HTTPException(status_code=400, detail="HR not found")

    new_job_posting = JobPostingTable(
        hr_id=current_user.user_id,
        job_title=job_posting.job_title,
        job_description=job_posting.job_description,
        company_name=job_posting.company_name,
        department=job_posting.department,
        location=job_posting.location,
        job_type=job_posting.job_type,
        experience_required=job_posting.experience_required,
        employment_type=job_posting.employment_type,
        requirements=job_posting.requirements,
        responsibilities=job_posting.responsibilities,
        salary_range=job_posting.salary_range,
        benefits=job_posting.benefits,
        application_deadline=job_posting.application_deadline,
        status=job_posting.status,
    )

    db.add(new_job_posting)
    db.commit()
    db.refresh(new_job_posting)

    return new_job_posting

@router.put("/published_job_post/{job_id}", response_model=None, dependencies=[Depends(JWTBearer()), Depends(get_admin_or_hr)])
async def published_job_post(job_id: int, db: Session = Depends(get_db)):
    try:
        job_posting = db.query(JobPostingTable).filter(JobPostingTable.id == job_id).first()
        if not job_posting:
            raise HTTPException(status_code=404, detail="Job posting not found")
        
        job_posting.is_published = True
        job_posting.status = 'Published'
        db.commit()
        db.refresh(job_posting)

        data = {
            "id": job_posting.id,
            "hr_id": job_posting.hr_id,
            "job_title": job_posting.job_title,
            "job_description": job_posting.job_description, 
            "company_name": job_posting.company_name, 
            "department": job_posting.department, 
            "location": job_posting.location,
            "job_type": job_posting.job_type.value if job_posting.job_type else None,  
            "experience_required": job_posting.experience_required,
            "employment_type": job_posting.employment_type.value if job_posting.employment_type else None, 
            "requirements": job_posting.requirements, 
            "responsibilities": job_posting.responsibilities, 
            "salary_range": job_posting.salary_range, 
            "benefits": job_posting.benefits,
            "application_deadline": job_posting.application_deadline, 
            "status": job_posting.status.value if job_posting.status else None,  
            "is_published": job_posting.is_published,
            "created_on": job_posting.created_on,
            "updated_on": job_posting.updated_on,
        }

        return data
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to verify material: {str(e)}")

@router.get("/get_all_job_postings/", response_model=None, dependencies=[Depends(JWTBearer()), Depends(get_admin_or_hr)])
def get_all_job_postings(db: Session = Depends(get_db)):
    try:
        job_postings = (
            db.query(JobPostingTable)
            .options(joinedload(JobPostingTable.user))    
            .all()
        )
        data = [
                    {
                        "id": job_posting.id,
                        "hr_id": job_posting.hr_id,
                        "hr_name": job_posting.user.user_name,
                        "job_title": job_posting.job_title,
                        "job_description": job_posting.job_description,
                        "company_name": job_posting.company_name,
                        "department": job_posting.department,
                        "location": job_posting.location,
                        "job_type": job_posting.job_type.value if job_posting.job_type else None,
                        "experience_required": job_posting.experience_required,
                        "employment_type": job_posting.employment_type.value if job_posting.employment_type else None,
                        "requirements": job_posting.requirements,
                        "responsibilities": job_posting.responsibilities,
                        "salary_range": job_posting.salary_range,
                        "benefits": job_posting.benefits,
                        "application_deadline": job_posting.application_deadline,
                        "status": job_posting.status.value if job_posting.status else None,
                        "is_published": job_posting.is_published,
                        "created_on": job_posting.created_on,
                        "updated_on": job_posting.updated_on,
                    }
                    for job_posting in job_postings
                ]

        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve job postings: {str(e)}")


@router.get("/get_all_published_job_postings/", response_model=None, dependencies=[Depends(JWTBearer()), Depends(get_admin_or_hr)])
def get_all_published_job_postings(db: Session = Depends(get_db)):
    try:
        job_postings = (
        db.query(JobPostingTable)
        .options(joinedload(JobPostingTable.user))  
        .filter(JobPostingTable.is_published == True)  
        .all()
    )
        
        data = [
            {
                "id": job_posting.id,
                "hr_id": job_posting.hr_id,
                "hr_name": job_posting.user.user_name,
                "job_title": job_posting.job_title,
                "job_description": job_posting.job_description,
                "company_name": job_posting.company_name,
                "department": job_posting.department,
                "location": job_posting.location,
                "job_type": job_posting.job_type.value if job_posting.job_type else None,
                "experience_required": job_posting.experience_required,
                "employment_type": job_posting.employment_type.value if job_posting.employment_type else None,
                "requirements": job_posting.requirements,
                "responsibilities": job_posting.responsibilities,
                "salary_range": job_posting.salary_range,
                "benefits": job_posting.benefits,
                "application_deadline": job_posting.application_deadline,
                "status": job_posting.status.value if job_posting.status else None,
                "is_published": job_posting.is_published,
                "created_on": job_posting.created_on,
                "updated_on": job_posting.updated_on,
            }
            for job_posting in job_postings
        ]

        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve job postings: {str(e)}")


@router.get("/job_postings/{job_id}", response_model=None)
def get_job_posting(job_id: int, db: Session = Depends(get_db)):
    job_posting = db.query(JobPostingTable).filter(JobPostingTable.id == job_id).first()
    if not job_posting:
        raise HTTPException(status_code=404, detail="Job posting not found")
    return job_posting

@router.patch("/job_postings/{job_id}", response_model=None, dependencies=[Depends(JWTBearer()), Depends(get_admin_or_hr)])
def update_job_posting(job_id: int, job_posting: JobPostingCreate, db: Session = Depends(get_db), current_user: AI_Interviewer = Depends(get_current_user)):
    existing_job_posting = db.query(JobPostingTable).filter(JobPostingTable.id == job_id).first()
    if not existing_job_posting:
        raise HTTPException(status_code=404, detail="Job posting not found")

    if job_posting.job_title is not None:
        existing_job_posting.job_title = job_posting.job_title
    if job_posting.job_description is not None:
        existing_job_posting.job_description = job_posting.job_description
    if job_posting.company_name is not None:
        existing_job_posting.company_name = job_posting.company_name
    if job_posting.department is not None:
        existing_job_posting.department = job_posting.department
    if job_posting.location is not None:
        existing_job_posting.location = job_posting.location
    if job_posting.job_type is not None:
        existing_job_posting.job_type = job_posting.job_type
    if job_posting.experience_required is not None:
        existing_job_posting.experience_required = job_posting.experience_required
    if job_posting.employment_type is not None:
        existing_job_posting.employment_type = job_posting.employment_type
    if job_posting.requirements is not None:
        existing_job_posting.requirements = job_posting.requirements
    if job_posting.responsibilities is not None:
        existing_job_posting.responsibilities = job_posting.responsibilities
    if job_posting.salary_range is not None:
        existing_job_posting.salary_range = job_posting.salary_range
    if job_posting.benefits is not None:
        existing_job_posting.benefits = job_posting.benefits
    if job_posting.application_deadline is not None:
        existing_job_posting.application_deadline = job_posting.application_deadline
    if job_posting.status is not None:
        existing_job_posting.status = job_posting.status

    db.add(existing_job_posting)
    db.commit()
    db.refresh(existing_job_posting)

    return existing_job_posting

@router.delete("/job_postings/{job_id}", response_model=None, dependencies=[Depends(JWTBearer()), Depends(get_admin_or_hr)])
def delete_job_posting(job_id: int, db: Session = Depends(get_db), current_user: AI_Interviewer = Depends(get_current_user)):
    job_posting = db.query(JobPostingTable).filter(JobPostingTable.id == job_id).first()
    if not job_posting:
        raise HTTPException(status_code=404, detail="Job posting not found")

    db.delete(job_posting)
    db.commit()

    return {f"detais":"Job posting deleted successfully", "job_posting_data":job_posting}

