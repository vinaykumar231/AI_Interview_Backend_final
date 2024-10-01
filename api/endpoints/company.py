from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Companies
from ..schemas import CompanyCreate, CompanyUpdate  

router = APIRouter()

@router.post("/companies/", response_model=CompanyCreate)
def create_company(company: CompanyCreate, db: Session = Depends(get_db)):
    db_company = Companies(**company.dict())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

@router.get("/companies/{company_id}", response_model=CompanyCreate)
def get_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Companies).filter(Companies.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

@router.put("/companies/{company_id}", response_model=CompanyUpdate)
def update_company(company_id: int, company_update: CompanyUpdate, db: Session = Depends(get_db)):
    company = db.query(Companies).filter(Companies.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    for key, value in company_update.dict().items():
        setattr(company, key, value)
    db.commit()
    db.refresh(company)
    return company

@router.delete("/companies/{company_id}")
def delete_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Companies).filter(Companies.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    db.delete(company)
    db.commit()
    return {"message": "Company deleted successfully"}