from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from ...models.resume import Resume
from database import get_db
from ...schemas import ResumeCreate, ResumeUpdate
import shutil
import fitz  # PyMuPDF for PDF
import mammoth  # For DOCX
import os
import uuid
import google.generativeai as genai  # Add the genai import
from pydantic import BaseModel
import json
from typing import Optional
from ...models.job_description import Job_Descriptions
from ...models.user import AI_Interviewer
from auth.auth_bearer import JWTBearer, get_admin, get_current_user
from ...models.company import Companies
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import os
import pytesseract
from pdf2image import convert_from_path
import re
from ...models.resume_analysis import Resume_Analysis
from typing import List
from ..Email_config import send_email
from ...models.student_level.resume_upload import Resume_upload
from ...models.student_level.resume_analysis import S_Resume_Analysis
from ...models.student_level.student_question import S_Question,generate_gemini_prompt_Question


load_dotenv()
router = APIRouter()


def save_file(upload_file: UploadFile) -> str:
    if not upload_file:
        return None

    try:
        unique_filename = str(uuid.uuid4()) + "_" + upload_file.filename
        file_path = os.path.join("static","student_level", "resume_check", unique_filename)
        
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

def generate_gemini_prompt(job_title: str, resume_text: str) -> str:
    prompt = f"""
    Evaluate the following resume against the provided job description and provide a detailed evaluation in a structured JSON format. Ensure that the JSON is valid and properly formatted, with all necessary commas included.

    **Job Description:** {job_title}  
    **Resume:** {resume_text}

    1. Extract the **email** and **phone number** from the resume.
    2. Include the contact information (email and phone number) in the JSON output.
    3. The JSON should be properly formatted, valid, and include all required commas and syntax.

    Please include the following keys in the JSON response:

    {{
        "overall_score": 0,
        "resume_score": 0,
        "resume_recommendations": [],
        "candidate_name": "",
        "candidate_email": "",
        "candidate_phone": "",
        "strengths": [],
        "weaknesses": [],
        "overall_suggestion": []
    }}

    ### Example Output:

    {{
        "overall_score": 85,
        "resume_score": 78,
        "resume_recommendations": [
            "Strong action verbs used",
            "Clearly defined skills section",
            "Good use of quantifiable results"
        ],
        "resume_missing_elements": [
            "Could benefit from a more impactful summary statement",
            "Consider adding relevant certifications"
        ],
        "candidate_name": "John Doe",
        "candidate_email": "john.doe@example.com",
        "candidate_phone": "555-555-5555",
        "strengths": ["Strong technical skills",
          "Excellent communication", 
          "Proven team player"],
        "weaknesses": [
            "Time management (working on it)",
            "Public speaking (seeking opportunities to improve)"
        ],
        "overall_suggestion": [
            "Consider adding a more impactful summary statement",
            "Consider adding relevant certifications"
        ],
        "candidate_info": {{
            "name": "John Doe",
            "email": "candidate@example.com",
            "phone": "+1234567890"
            }}
    }}

    Return the response as valid JSON format with proper commas and no syntax errors.
    """
    return prompt

generation_config={
  "type": "object",
  "properties": {
    "overall_score": {
      "type": "integer"
    },
    "resume_score": {
      "type": "integer"
    },
    "resume_recommendations": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "candidate_name": {
      "type": "string"
    },
    "candidate_email": {
      "type": "string"
    },
    "candidate_phone": {
      "type": "number"
    },
    "strengths": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "weaknesses": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "overall_suggestion": {
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  },
  "required": [
    "overall_score",
    "resume_score",
    "resume_recommendations",
    "candidate_name",
    "candidate_email",
    "candidate_phone",
    "strengths",
    "weaknesses",
    "overall_suggestion"
  ]
}

@router.post("/resume_upload/student_level/")
async def upload_files(
    job_title: str = Form(...),
    upload_resumes: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: AI_Interviewer = Depends(get_current_user)
):
    try:
            file_path = save_file(upload_resumes)
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

            prompt = generate_gemini_prompt(job_title, resume_text)
           
            model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
            response = model.generate_content(prompt)
            gemini_evaluation = response.text

            cleaned_response = clean_and_load_json(gemini_evaluation)
            
            resume_score=cleaned_response.get("resume_score")
            resume_recommendations=cleaned_response.get("resume_recommendations")
            resume_missing_elements=cleaned_response.get("resume_missing_elements")
            candidate_info = cleaned_response.get("candidate_info")
            if candidate_info:
                name = candidate_info.get("name")
                email = candidate_info.get("email")
                phone = candidate_info.get("phone")
            overall_score = cleaned_response.get("overall_score")
            overall_suggestion=cleaned_response.get("overall_suggestion")
            strengths = cleaned_response.get("strengths")
            weaknesses = cleaned_response.get("weaknesses")
        
            utc_now = pytz.utc.localize(datetime.utcnow())
            ist_now = utc_now.astimezone(pytz.timezone('Asia/Kolkata'))

            resume_entry = Resume_upload(
                user_id=current_user.user_id,
                file_path=file_path,
                resume_extract_data=resume_text.replace("```json", "").replace("\n", "").replace("```", "").replace("\\n", "").strip(),
                result=cleaned_response,
                uploaded_at=ist_now,
            )
            db.add(resume_entry)
            db.flush()

            resume_analysis_db = S_Resume_Analysis(
                resume_id=resume_entry.id,
                job_title=job_title,
                resume_score=resume_score,
                resume_recommendations=resume_recommendations,
                resume_missing_elements=resume_missing_elements,
                candidate_name=name,
                candidate_email=email,
                candidate_phone=phone,
                strengths=strengths,
                weaknesses=weaknesses,
                overall_score=overall_score,
                overall_suggestion=overall_suggestion,
                uploaded_at=ist_now,
                
            )
            db.add(resume_analysis_db)
            db.flush()
            db.commit()

            question_prompt = generate_gemini_prompt_Question(job_title)
            question_response = model.generate_content(question_prompt)
            gemini_question = clean_and_load_json(question_response.text)
            
            question_entry = S_Question(
                        resume_id=resume_entry.id,
                        candidate_name=name,
                        candidate_email=email,
                        Qustion1=gemini_question['experience_based_questions'][0],
                        Qustion2=gemini_question['experience_based_questions'][1],
                        Qustion3=gemini_question['behavioral_questions'][0],
                        Qustion4=gemini_question['behavioral_questions'][1],
                        Qustion5=gemini_question['cultural_fit_and_career_development_questions'][0],
                        is_ai_generated=True,
                        created_on=ist_now,
                    )
            db.add(question_entry)

            db.commit()
            data={
                "resume_id": resume_entry.id,
                "user_id": resume_entry.user_id,
                "resume_file_path": resume_entry.file_path,
                # "resume_extract_details": {
                # "resume_details": resume_text,
                #     },
                    "student_resume_result": {
                        "name":name,
                        "email":email,
                        "phone":phone,
                        "overall_score": overall_score,
                        "strengths": strengths,
                        "weaknesses": weaknesses,
                        "resume_recommendations": resume_recommendations,
                        "resume_missing_elements": resume_missing_elements,
                        "overall_suggestion":overall_suggestion
                       
                    },
                    "questions": {
                        "Qustion1": question_entry.Qustion1,
                        "Qustion2": question_entry.Qustion2,
                        "Qustion3": question_entry.Qustion3,
                        "Qustion4": question_entry.Qustion4,
                        "Qustion5": question_entry.Qustion5
                }
            }

    except Exception as e:
        raise HTTPException(status_code=404, detail=f"{e}")      

    # finally:
    #         if file_path and os.path.exists(file_path):
    #             os.remove(file_path)

    return data


@router.post("/send-selection-email/student/")
async def send_resume_selection_email(
    resume_ids: str,  
    send_to: str,     
    db: Session = Depends(get_db)
):
    resume_ids_list = resume_ids.split(',') 
    send_to_list = send_to.split(',')        
    results = {}

    for resume_id in resume_ids_list:
        resume_id = resume_id.strip() 
        
        resume_analysis = db.query(Resume_Analysis).filter(Resume_Analysis.resume_id == resume_id).first()

        if not resume_analysis:
            results[resume_id] = {"status": "Resume analysis not found", "recipients": []}
            continue  

        if resume_analysis.resume_selection_status != "resume selected":
            results[resume_id] = {"status": "Resume not selected", "recipients": []}
            continue  

        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            results[resume_id] = {"status": "Resume not found", "recipients": []}
            continue  

        # Prepare email body with candidate information
        email_body_selected = f"""
            <p>Dear {resume_analysis.candidate_name},</p>
             <p>Congratulations! Your resume for the position of <strong>{resume_analysis.job_title}</strong> has been selected for the next round of the interview process. 
             </p>
             <p>Please click on the link below to schedule your interview:</p>
            <a href="https://your-domain.com/schedule-interview/{resume_id}">Schedule Interview</a>
            <br>
            <p><strong>Disclaimer:</strong> This email is confidential. If you are not the intended recipient, please let the sender know and delete this email.</p>
            <br>
            <p>Best regards,</p>
            <p>Vinay Kumar</p>
            <p>MaitriAI</p>
            <p>900417181</p>
        """

        results[resume_id] = {"status": "Emails sent", "recipients": []}

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
                    results[resume_id]["recipients"].append({"recipient": recipient, "status": "Email sent successfully"})
                except Exception as e:
                    results[resume_id]["recipients"].append({"recipient": recipient, "status": f"Failed to send email: {str(e)}"})

    return {
        "message": "Selection emails processed",
        "results": results
    }

@router.get("/selected-resumes/student/", response_model=None)
async def get_selected_resumes(db: Session = Depends(get_db)):
    selected_resumes = db.query(Resume_Analysis).filter(Resume_Analysis.resume_selection_status == "resume selected").all()

    if not selected_resumes:
        raise HTTPException(status_code=404, detail="No selected resumes found")
    all_candidate=[]
    for candidate in selected_resumes:
        data={
            "resume_id":candidate.resume_id,
            "Job Title":candidate.job_title,
            "candidate_name": candidate.candidate_name,
            "candidate_email": candidate.candidate_email,
            "candidate_phone": candidate.candidate_phone,
            "candidate_overall_score": candidate.overall_score,
            "candidate_resume_selection_status": candidate.resume_selection_status,
        }
        all_candidate.append(data)
    return all_candidate

