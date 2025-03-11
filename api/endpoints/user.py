from datetime import datetime, timedelta
import jwt
from fastapi import APIRouter, Depends, HTTPException,Form
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session
from api.models.report import Report
from auth.auth_bearer import JWTBearer, get_admin, get_current_user
from database import get_db, api_response
from ..models.user import AI_Interviewer
from ..schemas import LoginInput, ChangePassword, UserCreate, UpdateUser, UserType
import bcrypt
from .Email_config import send_email
import random
import pytz
from ..models.company import Companies
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter()

user_ops = AI_Interviewer()


def generate_token(data):
    exp = datetime.utcnow() + timedelta(days=1)
    token_payload = {'user_id': data['emp_id'], 'exp': exp}
    token = jwt.encode(token_payload, 'cat_walking_on_the street', algorithm='HS256')
    return token, exp


@router.post('/AI_Interviewers/login/')
async def AI_Interviewers(credential: LoginInput):
    try:
        response = user_ops.AI_Interviewers_login(credential)
        return response
    except HTTPException as e:
        raise
    except Exception as e:
        return HTTPException(status_code=500, detail=f"login failed: {str(e)}")


@router.post("/insert/ai_Interviewer_register/", dependencies=[Depends(JWTBearer()), Depends(get_admin)])
def AI_Interviewer_register(data: UserCreate, db: Session = Depends(get_db)):
    try:
        if not AI_Interviewer.validate_email(data.user_email):
            raise HTTPException(status_code=400, detail="Invalid email format")

        if not AI_Interviewer.validate_password(data.user_password):
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")

        if not AI_Interviewer.validate_phone_number(data.phone_no):
            raise HTTPException(status_code=400, detail="Phone Number must be  10 digit")

        utc_now = pytz.utc.localize(datetime.utcnow())
        ist_now = utc_now.astimezone(pytz.timezone('Asia/Kolkata'))

        hashed_password = bcrypt.hashpw(data.user_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        usr = AI_Interviewer(
            user_name=data.user_name,
            user_email=data.user_email,
            user_password=hashed_password,
            company_name=data.company_name,
            industry=data.industry,
            user_type=UserType.HR,  
            phone_no=data.phone_no,
            created_on=ist_now,
            updated_on=ist_now
        )
        db.add(usr)
        db.flush()  

        company_db = Companies(
            hr_id=usr.user_id,  
            company_name=data.company_name,
            industry=data.industry
        )
        db.add(company_db)
        db.commit()

        response = api_response(200, message="User Created successfully")
        return response
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=404, detail=f"filed to hr Register")

@router.post("/insert/student_level_register/")
def AI_Interviewer_register(
            user_name: str = Form(None),
            user_email: str = Form(None),
            user_password: str = Form(...),
            user_type: str = UserType.Students,
            phone_no: str = Form(...),
            db: Session = Depends(get_db)):
    try:
        if not AI_Interviewer.validate_email(user_email):
            raise HTTPException(status_code=400, detail="Invalid email format")

        if not AI_Interviewer.validate_password(user_password):
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")

        if not AI_Interviewer.validate_phone_number(phone_no):
            raise HTTPException(status_code=400, detail="Invalid phone number")

        utc_now = pytz.utc.localize(datetime.utcnow())
        ist_now = utc_now.astimezone(pytz.timezone('Asia/Kolkata'))

        user_email_exist= db.query(AI_Interviewer).filter(AI_Interviewer.user_email==user_email).first()
        if user_email_exist:
            raise HTTPException(status_code=400, detail=" User Email already exist in database")

        hashed_password = bcrypt.hashpw(user_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        usr = AI_Interviewer(
            user_name=user_name,
            user_email=user_email,
            user_password=hashed_password,
            user_type=user_type,  
            phone_no=phone_no,
            created_on=ist_now,
            updated_on=ist_now
        )
        db.add(usr)
        db.commit()

        response = api_response(200, message="User Created successfully")
        return response
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="A database error occurred while register.")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="An unexpected error occurred  while register.")

@router.get("/get_all_users/", dependencies=[Depends(JWTBearer()), Depends(get_admin)])
def get_current_user_details( db: Session = Depends(get_db)):
    try:
        all_user=[]
        user_db=db.query(AI_Interviewer).all()
        for user in user_db:
            user_details = {
                "user_id": user.user_id,
                "username": user.user_name,
                "email": user.user_email,
                "user_type": user.user_type,
                "phone_no" : user.phone_no,
                "company" : user.company_name,
                "industry" : user.industry,

            }
            all_user.append(user_details)
        return all_user
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    
@router.get("/get_all_hr_count_with_candidate/",dependencies=[Depends(JWTBearer()), Depends(get_admin)])
def get_all_hr_count_with_candidate(db: Session = Depends(get_db)):
    reports = (
        db.query(Report)
        .options(joinedload(Report.user))  
        .all()
    )

    # Aggregate data
    hr_data = {}
    for report in reports:
        hr_id = report.hr_id
        hr_name = report.user.user_name if report.user else "Unknown HR"  

        if hr_id not in hr_data:
            hr_data[hr_id] = {
                "hr_id": hr_id,
                "hr_name": hr_name,
                "candidate_count": 0,
                "candidate_names": []
            }
        
        hr_data[hr_id]["candidate_count"] += 1
        if report.candidate_name:
            hr_data[hr_id]["candidate_names"].append(report.candidate_name)

    hr_counts = list(hr_data.values())
    for hr in hr_counts:
        hr["candidate_names"] = sorted(hr["candidate_names"])  

    response = {
        "hr_counts": hr_counts,
    }

    return response


@router.get("/read/user", dependencies=[Depends(JWTBearer()), Depends(get_admin)])
async def searchall(user_id: int = None, user_type: UserType = None, page_num: int = 1, page_size: int = 20,
                    db: Session = Depends(get_db)):
    return user_ops.searchall(user_id, user_type, page_num, page_size, db)


@router.get("/get_my_profile")
def get_current_user_details(current_user: AI_Interviewer = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        user_details = {
            # "user_id": current_user.user_id,
            "username": current_user.user_name,
            "email": current_user.user_email,
            "user_type": current_user.user_type,
            "company_name": current_user.company_name,
            "industry": current_user.industry,
            "phone_no" : current_user.phone_no,

        }
        return api_response(data=user_details, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    
class UserTypeUpdate(BaseModel):
    user_id: int
    user_type: str

@router.put("/update_user_type/")
async def update_user_type(update: UserTypeUpdate, db: Session = Depends(get_db)):
    # Check if user exists
    user = db.query(AI_Interviewer).filter(AI_Interviewer.user_id == update.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update the user type
    user.user_type = update.user_type
    db.commit()
    return {"message": "User type updated successfully"}

@router.delete("/delete_user/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(AI_Interviewer).filter(AI_Interviewer.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    return {"message": f"User with ID {user_id} deleted successfully"}

@router.put("/update/lms_user/{user_id}", dependencies=[Depends(JWTBearer())])
async def lms_user_update(user_data: UpdateUser, user_id: int,
                          current_user: AI_Interviewer = Depends(get_current_user),
                          db: Session = Depends(get_db)):
    try:
        if user_data.user_type and user_data.user_type not in {"user", "admin", "teacher", "student", "parent"}:
            raise HTTPException(status_code=403, detail="Invalid user type. Allowed values: user, admin, teacher, student, parent")

        if current_user.user_type == "admin" or current_user.user_id == user_id:
            db_user = db.query(AI_Interviewer).filter(AI_Interviewer.user_id == user_id, AI_Interviewer.is_deleted == False).first()
            if db_user is None:
                raise HTTPException(status_code=404, detail="Record not found")

            if user_data.user_email:
                existing_user = db.query(AI_Interviewer).filter(
                    AI_Interviewer.user_email == user_data.user_email,
                    AI_Interviewer.user_id != user_id
                ).first()
                if existing_user:
                    raise HTTPException(status_code=400, detail="Email already exists for another user")

            hero_data = user_data.dict(exclude_unset=True)
            for key, value in hero_data.items():
                setattr(db_user, key, value)

            is_administrator: bool = current_user.user_type == "admin"

            if (is_administrator and user_data.new_password) or (
                    not is_administrator and user_data.current_password and user_data.new_password):
                if not user_ops.validate_password(user_data.new_password):
                    raise HTTPException(status_code=400, detail="Invalid new password")

                current_password = None if is_administrator else user_data.current_password
                user_ops.change_password(current_password, user_data.new_password, user_id, is_administrator, db)

            db.commit()
            response = api_response(200, message="User Data updated successfully")
            return response
        else:
            raise HTTPException(status_code=403, detail="Forbidden: You are not authorized to update this user's data.")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

#######################################################################################

@staticmethod
def validate_password(password):
        return len(password) >= 8


@router.put("/change_password/{user_id}")
async def change_password(current_password: str, new_password: str, confirm_new_password: str, current_user: AI_Interviewer = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        if new_password != confirm_new_password:
            raise HTTPException(status_code=400, detail="New passwords do not match")

        user = db.query(AI_Interviewer).filter(AI_Interviewer.user_id == current_user.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User with ID {current_user.user_id} not found")

        if not bcrypt.checkpw(current_password.encode('utf-8'), user.user_password.encode('utf-8')):
            raise HTTPException(status_code=400, detail="Wrong current password")

        if not user_ops.validate_password(new_password):
            raise HTTPException(status_code=400, detail="Invalid new password")
        
        hashed_new_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        user.user_password = hashed_new_password

        db.commit()
        contact = "900-417-3181"
        email_contact = "vinay@example.com"

        reset_email_body = f"""
        <p>Dear User,</p>
        <p>Your password has been successfully changed.</p>
        <p>If you did not request this change, please contact support at {contact} or email us at {email_contact}.</p>
        <p>Thank you!</p>
        <br><br>
        <p>Best regards,</p>
        <p>Vinay Kumar</p>
        <p>MaitriAI</p>
        <p>900417181</p>
        """
        await send_email(
            subject="Password Change Confirmation",
            email_to=user.user_email,
            body=reset_email_body
        )
        return {"message": "Password changed successfully"}

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")



def generate_otp():
    return random.randint(100000, 999999)

async def send_otp_email(email: str, otp: int):
    otp_email_body = f"""
    <p>Dear User,</p>
    <p>Your OTP for password reset is: <strong>{otp}</strong></p>
    <p>Please use this OTP to reset your password.</p>
    <br><br>
    <p>Best regards,</p>
    <p>Vinay Kumar</p>
    <p>MaitriAI</p>
    <p>900417181</p>
    """
    await send_email(
        subject="Password Reset OTP",
        email_to=email,
        body=otp_email_body
    )

@router.post("/send_otp")
async def send_otp(email: str, db: Session = Depends(get_db)):
    user = db.query(AI_Interviewer).filter(AI_Interviewer.user_email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User with email {email} not found")

    otp = generate_otp()
    utc_now = pytz.utc.localize(datetime.utcnow())
    ist_now = utc_now.astimezone(pytz.timezone('Asia/Kolkata'))
    
    user.reset_otp = otp
    user.otp_generated_at = ist_now
    
    db.commit()

    await send_otp_email(email, otp)
    return {"message": "OTP sent successfully"}

@router.put("/reset_password")
async def forgot_password(email: str, new_password: str, confirm_new_password: str, db: Session = Depends(get_db)):
    try:
        if new_password != confirm_new_password:
            raise HTTPException(status_code=400, detail="Passwords do not match")

        user = db.query(AI_Interviewer).filter(AI_Interviewer.user_email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User with email {email} not found")
        
        if not validate_password(new_password):
            raise HTTPException(status_code=400, detail="Invalid new password")

        hashed_new_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        user.user_password = hashed_new_password

        db.commit()

        # Send email for password reset
        contact = "900-417-3181"
        email_contact = "vinay@example.com"

        reset_email_body = f"""
        <p>Dear User,</p>
        <p>Your password has been successfully changed.</p>
        <p>If you did not request this change, please contact support at {contact} or email us at {email_contact}.</p>
        <p>Thank you!</p>
        <br><br>
        <p>Best regards,</p>
        <p>Vinay Kumar</p>
        <p>MaitriAI</p>
        <p>900417181</p>
        """
        await send_email(
            subject="Password Reset Request",
            email_to=email,
            body=reset_email_body
        )

        return {"message": "Password reset successfully"}

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")