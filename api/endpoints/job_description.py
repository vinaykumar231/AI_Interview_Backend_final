from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models import Job_Descriptions
from database import get_db
from schemas import JDCreate, JDUpdate

router = APIRouter()

@router.post("/job_descriptions/", response_model=JDCreate)
def create_job_description(jd: JDCreate, db: Session = Depends(get_db)):
    job_description = Job_Descriptions(**jd.dict())
    db.add(job_description)
    db.commit()
    db.refresh(job_description)
    return job_description

@router.get("/job_descriptions/{jd_id}", response_model=JDCreate)
def get_job_description(jd_id: int, db: Session = Depends(get_db)):
    jd = db.query(Job_Descriptions).filter(Job_Descriptions.id == jd_id).first()
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found")
    return jd

@router.put("/job_descriptions/{jd_id}", response_model=JDUpdate)
def update_job_description(jd_id: int, jd_update: JDUpdate, db: Session = Depends(get_db)):
    jd = db.query(Job_Descriptions).filter(Job_Descriptions.id == jd_id).first()
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found")
    for key, value in jd_update.dict().items():
        setattr(jd, key, value)
    db.commit()
    db.refresh(jd)
    return jd

@router.delete("/job_descriptions/{jd_id}")
def delete_job_description(jd_id: int, db: Session = Depends(get_db)):
    jd = db.query(Job_Descriptions).filter(Job_Descriptions.id == jd_id).first()
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found")
    db.delete(jd)
    db.commit()
    return {"message": "Job description deleted successfully"}
