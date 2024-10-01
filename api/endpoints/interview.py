from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models import Interview
from database import get_db
from schemas import InterviewCreate, InterviewUpdate

router = APIRouter()

@router.post("/interviews/", response_model=InterviewCreate)
def schedule_interview(interview: InterviewCreate, db: Session = Depends(get_db)):
    interview_data = Interview(**interview.dict())
    db.add(interview_data)
    db.commit()
    db.refresh(interview_data)
    return interview_data

@router.get("/interviews/{interview_id}", response_model=InterviewCreate)
def get_interview(interview_id: int, db: Session = Depends(get_db)):
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    return interview

@router.put("/interviews/{interview_id}", response_model=InterviewUpdate)
def update_interview(interview_id: int, interview_update: InterviewUpdate, db: Session = Depends(get_db)):
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    for key, value in interview_update.dict().items():
        setattr(interview, key, value)
    db.commit()
    db.refresh(interview)
    return interview

@router.delete("/interviews/{interview_id}")
def delete_interview(interview_id: int, db: Session = Depends(get_db)):
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    db.delete(interview)
    db.commit()
    return {"message": "Interview deleted successfully"}
