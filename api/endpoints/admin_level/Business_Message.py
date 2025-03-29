from datetime import datetime, timedelta
import jwt
from fastapi import APIRouter, Depends, HTTPException,Form
import pytz
from sqlalchemy import func
from sqlalchemy.orm import Session
from api.models.admin_level.Business_Message import Business_message
from api.models.report import Report
from api.schemas import CompanyCreate
from auth.auth_bearer import JWTBearer, get_admin, get_current_user
from database import get_db, api_response

router = APIRouter()


@router.post("/companies/", response_model=None)
def create_company(company: CompanyCreate, db: Session = Depends(get_db)):
    try:
        utc_now = pytz.utc.localize(datetime.utcnow())
        ist_now = utc_now.astimezone(pytz.timezone('Asia/Kolkata'))
        db_company = Business_message(**company.dict(), created_on=ist_now)
        db.add(db_company)
        try:
            db.commit()
            db.refresh(db_company)
        except Exception as e:
            db.rollback()  
        return db_company
    except:
        raise HTTPException(status_code=404, detail="failed to submmit")

# GET API
@router.get("/companies/", response_model=None,dependencies=[Depends(JWTBearer()), Depends(get_admin)])
def get_companies(db: Session = Depends(get_db)):
    return db.query(Business_message).all()

@router.put("/verify_company_details/{message_id}")
async def verify_material(message_id: int, db: Session = Depends(get_db)):
    try:
        message = db.query(Business_message).filter(Business_message.id == message_id).first()
        
        if not message:
            raise HTTPException(status_code=404, detail="message not found")
        
        message.is_checked = True
        message.status = 'checked'  
        db.commit()  
        db.refresh(message)

        return {f"message: cheked secessfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to verify material: {str(e)}")
    
@router.delete("/companies/{company_id}", response_model=None)
def delete_company(company_id: int, db: Session = Depends(get_db)):
    # Try to find the company by ID
    db_company = db.query(Business_message).filter(Business_message.id == company_id).first()
    
    if db_company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    
    try:
        # Delete the company from the database
        db.delete(db_company)
        db.commit()
        return {"message": "Company deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete company")
