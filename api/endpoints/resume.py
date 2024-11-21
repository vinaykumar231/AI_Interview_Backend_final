from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from ..models.resume import Resume
from database import get_db
from ..schemas import ResumeCreate, ResumeUpdate
import shutil
import fitz  # PyMuPDF for PDF
import mammoth  # For DOCX
import os
import uuid
import google.generativeai as genai  # Add the genai import
from pydantic import BaseModel
import json
from typing import Optional
from ..models.job_description import Job_Descriptions
from ..models.user import AI_Interviewer
from auth.auth_bearer import JWTBearer, get_admin, get_current_user
from ..models.company import Companies
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import os
import pytesseract
from pdf2image import convert_from_path
import re
from ..models.resume_analysis import Resume_Analysis
from typing import List
from ..models.question import generate_gemini_prompt_Question,Question
from .Email_config import send_email
from ..models.interview_scheduled_data import InterviewScheduledData
from sqlalchemy.orm import Session, joinedload


load_dotenv()
router = APIRouter()

base_url_path = os.getenv("BASE_URL_PATH")

def save_file(upload_file: UploadFile) -> str:
    if not upload_file:
        return None

    try:
        unique_filename = str(uuid.uuid4()) + "_" + upload_file.filename
        file_path = os.path.join("static", "selected_resume", unique_filename)
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)

        return file_path.replace("\\", "/")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")


def clean_and_load_json(raw_response: str):
    cleaned_response = raw_response.replace("```", "").replace("json", "").replace("\\n", "").strip()
    try:
        data = json.loads(cleaned_response)

        return data
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=404, detail="Due to Technical Error file not read correct. Please try again.")
    

def extract_text_from_pdf(file_path: str) -> str:
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text("text")
        return text
    except Exception as e:
        return ""

def extract_text_with_ocr(file_path: str) -> str:
    try:
        images = convert_from_path(file_path)
        text = ""
        for image in images:
            text += pytesseract.image_to_string(image)
        return text
    except Exception as e:
        return ""

def extract_text_from_docx(file_path: str) -> str:
    try:
        with open(file_path, "rb") as docx_file:
            result = mammoth.extract_raw_text(docx_file)
            text = result.value
        return text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting text from DOCX: {str(e)}")

def generate_gemini_prompt(job_description: str, resume_text: str) -> str:
    prompt = f"""
**Modified Prompt:**

Evaluate the following resume against the provided job description and provide a detailed evaluation in a structured JSON format. Ensure that the JSON is valid and properly formatted, with all necessary commas included.

**Job Description:** {job_description}  
**Resume:** {resume_text}

1. Extract the **email** and **phone number** from the resume.
2. Include the contact information (email and phone number) in the JSON output.
3. The JSON should be properly formatted, valid, and include all required commas and syntax.


Please include the following keys in the JSON response:

{{
  "overall_score": <numeric value between 0 and 100>,
  "relevance": <numeric score between 0 and 10>,
  "skills_fit": <numeric score between 0 and 10>,
  "experience_match": <numeric score between 0 and 10>,
  "cultural_fit": <numeric score between 0 and 10>,
  "strengths": <list of key strengths>,
  "weaknesses": <list of key weaknesses or gaps>,
  "missing_elements": <list of key missing qualifications or experiences>,
  "recommendations": <list of suggestions for improvement>
}}

### Example Output:

{{
  "overall_score": 85,
  "relevance": 9,
  "skills_fit": 8,
  "experience_match": 7,
  "cultural_fit": 6,
  "strengths": ["Strong technical skills", "Excellent communication", "Proven team player"],
  "weaknesses": ["Limited project management experience", "No certifications in relevant technologies"],
  "missing_elements": ["Experience with agile methodologies", "Leadership roles"],
  "recommendations": ["Consider obtaining project management certification", "Gain experience in agile environments"]
   "candidate_info": {{
    "name": "John Doe",
    "email": "candidate@example.com",
    "phone": "+1234567890"
}}
}}

Return the response as valid JSON format with proper commas and no syntax errors. 
"""
    return prompt


@router.post("/resume_upload/")
async def upload_files(
    job_title: str = Form(...),
    job_description: str = Form(...),
    upload_resumes: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: AI_Interviewer = Depends(get_current_user)
):
    results = []
    try:
        for upload_resume in upload_resumes:
            file_path = save_file(upload_resume)
            if not file_path or not os.path.isfile(file_path):
                raise HTTPException(status_code=400, detail="Failed to save the uploaded file")

            file_size = os.path.getsize(file_path)

            if file_size == 0:
                raise HTTPException(status_code=400, detail="The uploaded file is empty")

            if file_path.lower().endswith(".pdf"):
                resume_text = extract_text_from_pdf(file_path)
                if not resume_text.strip():
                    resume_text = extract_text_with_ocr(file_path)
            elif file_path.lower().endswith(".docx"):
                resume_text = extract_text_from_docx(file_path)
            else:
                raise HTTPException(status_code=400, detail="Unsupported file type")

            if not resume_text or not resume_text.strip():
                resume_text = "No readable text could be extracted from this file."

            genai.configure(api_key=os.environ["API_KEY_gm"])

            prompt = generate_gemini_prompt(job_description, resume_text)
           
            model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
            response = model.generate_content(prompt)
            gemini_evaluation = response.text

            cleaned_response = clean_and_load_json(gemini_evaluation)

            candidate_info = cleaned_response.get("candidate_info")
            if candidate_info:
                name = candidate_info.get("name")
                email = candidate_info.get("email")
                phone = candidate_info.get("phone")
                
            overall_score = cleaned_response.get("overall_score")
            relevance_score = cleaned_response.get("relevance")
            strengths = cleaned_response.get("strengths")
            skills_fit_score = cleaned_response.get("skills_fit")
            weaknesses = cleaned_response.get("weaknesses")
            cultural_fit_score = cleaned_response.get("cultural_fit")
            recommendations = cleaned_response.get("recommendations")
            experience_match_score = cleaned_response.get("experience_match")
            missing_elements = cleaned_response.get("missing_elements")

            company = db.query(Companies).filter(Companies.hr_id == current_user.user_id).first()
            if not company:
                raise HTTPException(status_code=404, detail="No company found for the current user")

            utc_now = pytz.utc.localize(datetime.utcnow())
            ist_now = utc_now.astimezone(pytz.timezone('Asia/Kolkata'))

            resume_entry = Resume(
                company_id=company.id,
                user_id=current_user.user_id,
                candidate_email=email,
                file_path=file_path,
                resume_extract_data=resume_text.replace("```json", "").replace("\n", "").replace("```", "").replace("\\n", "").strip(),
                result=cleaned_response,
                uploaded_at=ist_now,
            )
            db.add(resume_entry)
            db.flush()

            SCORE_THRESHOLD = int(os.getenv('SCORE_THRESHOLD', 75))
            RESUME_SELECTED_MESSAGE = os.getenv('RESUME_SELECTED_MESSAGE', 'resume selected')
            RESUME_REJECTED_MESSAGE = os.getenv('RESUME_REJECTED_MESSAGE', 'resume rejected')
            
            resume_status = RESUME_SELECTED_MESSAGE if overall_score >= SCORE_THRESHOLD else RESUME_REJECTED_MESSAGE

            resume_analysis_db = Resume_Analysis(
                resume_id=resume_entry.id,
                job_title=job_title,
                hr_id=current_user.user_id,
                candidate_name=name,
                candidate_email=email,
                candidate_phone=phone,
                overall_score=overall_score,
                relevance_score=relevance_score,
                experience_match_score=experience_match_score,
                cultural_fit_score=cultural_fit_score,
                strengths=strengths,
                weaknesses=weaknesses,
                recommendations=recommendations,
                missing_elements=missing_elements,
                uploaded_at=ist_now,
                resume_selection_status=resume_status,
            )
            db.add(resume_analysis_db)
            db.flush()

            job_description_db = Job_Descriptions(
                company_id=company.id,
                user_id=current_user.user_id,
                job_title=job_title,
                job_description=job_description,
                created_on=ist_now,
            )
            db.add(job_description_db)
            db.commit()

            if resume_status == 'resume selected':
                question_prompt = generate_gemini_prompt_Question(job_description)
                question_response = model.generate_content(question_prompt)
                gemini_question = clean_and_load_json(question_response.text)

                question_entry = Question(
                    resume_id=resume_entry.id,
                    candidate_name=name,
                    candidate_email=email,
                    resume_selection_status=resume_status,
                    Qustion1=gemini_question.get('experience_based_questions', [None])[0],
                    Qustion2=gemini_question.get('experience_based_questions', [None])[1],
                    Qustion3=gemini_question.get('behavioral_questions', [None])[0],
                    Qustion4=gemini_question.get('behavioral_questions', [None])[1],
                    Qustion5=gemini_question.get('cultural_fit_and_career_development_questions', [None])[0],
                    is_ai_generated=True,
                    created_on=ist_now,
                )
                db.add(question_entry)
                db.commit()

            results.append({
                "resume_id": resume_entry.id,
                "name": name,
                "filename": upload_resume.filename,
                "company_id": resume_entry.company_id,
                "hr_id": resume_entry.user_id,
                "resume_file_path": resume_entry.file_path,
                "job_description": {
                    "job_title": job_description_db.job_title,
                    "job_description": job_description_db.job_description,
                },
                "resume_selection_result": {
                    "candidate_info": {
                        "name": name,
                        "email": email,
                        "phone": phone,
                    },
                    "questions": {
                        "generated_questions": {
                            "resume_id": resume_entry.id,
                            "resume_selection_status": resume_status,
                            "all_questions": {
                                "Qustion1": question_entry.Qustion1,
                                "Qustion2": question_entry.Qustion2,
                                "Qustion3": question_entry.Qustion3,
                                "Qustion4": question_entry.Qustion4,
                                "Qustion5": question_entry.Qustion5,
                            } if resume_status == 'resume selected' else None,
                        },
                    },
                    "overall_score": overall_score,
                    "relevance_score": relevance_score,
                    "cultural_fit_score": cultural_fit_score,
                    "skills_fit_score": skills_fit_score,
                    "experience_match_score": experience_match_score,
                    "strengths": strengths,
                    "weaknesses": weaknesses,
                    "recommendations": recommendations,
                    "missing_elements": missing_elements,
                    "resume_selection_status": resume_status,
                },
            })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    
    return results

@router.post("/send-selection-email/")
async def send_resume_selection_email(
    #resume_ids: str,  
    send_to: str,     
    db: Session = Depends(get_db)
):
    #resume_ids_list = resume_ids.split(',') 
    send_to_list = send_to.split(',')        
    results = {}

    for email in send_to_list:
        candidate_email = email.strip() 
        
        resume_analysis = db.query(Resume_Analysis).options(joinedload(Resume_Analysis.user)).filter(Resume_Analysis.candidate_email == email).first()


        if resume_analysis.resume_selection_status != "resume selected":
            results[candidate_email] = {"status": "Resume not selected", "recipients": []}
            continue  

        resume = db.query(Resume).filter(Resume.candidate_email == candidate_email).first()
        if not resume:
            results[candidate_email] = {"status": "Resume not found", "recipients": []}
            continue  

        # Prepare email body with candidate information
        email_body_selected = f"""
            <p>Dear {resume_analysis.candidate_name},</p>
             <p>Congratulations! Your resume for the position of <strong>{resume_analysis.job_title}</strong> at <strong>{resume_analysis.user.company_name}</strong> has been selected for the next round of the interview process. 
             </p>
             <p>Please click on the link below to schedule your interview:</p>
            <a href="http://localhost:3000/candidate_Interview">Interview link</a>
            <br>
            <p><strong>Disclaimer:</strong> This email is confidential. If you are not the intended recipient, please let the sender know and delete this email.</p>
            <br>
            <p>Best regards,</p>
            <p>Vinay Kumar</p>
            <p>MaitriAI</p>
            <p>900417181</p>
        """

        results[candidate_email] = {"status": "Emails sent", "recipients": []}

        # Send emails to each recipient for this resume ID
        for recipient in send_to_list:
            recipient = recipient.strip()  
            if recipient:  
                try:
                    await send_email(
                        subject="Resume Selection Notification",
                        email_to=recipient,
                        body=email_body_selected
                    )
                    results[candidate_email]["recipients"].append({"recipient": recipient, "status": "Email sent successfully"})
                except Exception as e:
                    results[candidate_email]["recipients"].append({"recipient": recipient, "status": f"Failed to send email: {str(e)}"})

    return {
        "message": "Selection emails processed",
        "results": results
    }


def validate_date_format(date_str: str) -> bool:
    """Validate if the date string matches YYYY-MM-DD format"""
    pattern = r'^\d{4}-\d{2}-\d{2}$'
    if not re.match(pattern, date_str):
        return False
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def validate_time_format(time_str: str) -> bool:
    """Validate if the time string matches HH:MM format"""
    pattern = r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'
    return bool(re.match(pattern, time_str))

@router.post("/schedule-interview/")
async def schedule_interview(
    #hr_email: str, 
    candidate_email: str = Form(...),
    interview_date: str = Form(...),
    interview_time: str = Form(...),
    db: Session = Depends(get_db)
):
    
     # Validate date format
    if not validate_date_format(interview_date):
        raise HTTPException(status_code=400, detail="Invalid date format. Please use YYYY-MM-DD format (e.g., 2024-11-15)")
    
    # Validate time format
    if not validate_time_format(interview_time):
        raise HTTPException(status_code=400,detail="Invalid time format. Please use HH:MM format (e.g., 14:30)")
    
    utc_now = pytz.utc.localize(datetime.utcnow())
    ist_now = utc_now.astimezone(pytz.timezone('Asia/Kolkata'))

    candidate = db.query(Resume_Analysis).options(joinedload(Resume_Analysis.user)).filter(Resume_Analysis.candidate_email == candidate_email).first()
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found with the provided email.")
    
    interview_data=InterviewScheduledData(
        #hr_email=hr_email,
        candidate_email=candidate_email,
        candidate_name=candidate.candidate_name,
        interview_date = interview_date,
        interview_time = interview_time,
        created_on=ist_now,
        updated_on=ist_now
    )
    db.add(interview_data)
    db.commit()
    
    body = f"""
    <h3>Interview Scheduled</h3>
    <p>The candidate <b>{interview_data.candidate_name}</b> has successfully scheduled their interview.</p>
    <p><b>Date:</b> {interview_date}</p>
    <p><b>Time:</b> {interview_time}</p>
    <p>Candidate Email: {interview_data.candidate_email}</p>
    <p>Candidate Phone: {candidate.candidate_phone}</p>
    <p>Thank you!</p>
    <br>
    <p>Best regards,</p>
    <p>Vinay Kumar</p>
    <p>MaitriAI</p>
    <p>900417181</p>
    """
    
    try:
        await send_email(
            subject="Interview Scheduled Notification",
            email_to=candidate.user.user_email,  
            body=body
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
    
    return {"message": "Interview scheduled successfully. HR has been notified."}

@router.get("/selected-resumes/", response_model=List[dict])
async def get_selected_resumes(db: Session = Depends(get_db), current_user: AI_Interviewer = Depends(get_current_user)):
    selected_resumes = db.query(Resume_Analysis) \
        .options(joinedload(Resume_Analysis.user)) \
        .filter(Resume_Analysis.resume_selection_status == "resume selected",
                Resume_Analysis.hr_id == current_user.user_id) \
        .all()

    if not selected_resumes:
        raise HTTPException(status_code=404, detail="No selected resumes found")
    
    all_candidate = []
    for candidate in selected_resumes:
        data = {
            "resume_id": candidate.resume_id,
            "hr_id": candidate.user.user_id,
            "hr_name": candidate.user.user_name,
            "hr_email": candidate.user.user_email,
            "company_name": candidate.user.company_name,
            "job_title": candidate.job_title,
            "candidate_name": candidate.candidate_name,
            "candidate_email": candidate.candidate_email,
            "candidate_phone": candidate.candidate_phone,
            "candidate_overall_score": candidate.overall_score,
            "candidate_resume_selection_status": candidate.resume_selection_status,
        }
        all_candidate.append(data)

    return all_candidate

@router.get("/questions-by-email/{candidate_email}", response_model=None)
async def get_questions_by_email(candidate_email: str, db: Session = Depends(get_db)):
    try:
        all_data=[]
        questions = db.query(Question).filter(Question.candidate_email == candidate_email).all()
        if not questions:
            raise HTTPException(status_code=404, detail="No questions found for this email")
        for q in questions:
            data={
                "Qustion1":q.Qustion1,
                "Qustion2":q.Qustion2,
                "Qustion3":q.Qustion3,
                "Qustion4":q.Qustion4,
                "Qustion5":q.Qustion5,
                "candidate_email":q.candidate_email,
            }
            all_data.append(data)
        return all_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while retrieving the questions: {str(e)}")
