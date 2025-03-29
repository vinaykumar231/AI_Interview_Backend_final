from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session

from api.models.candidate_level.report import Candidate_Report
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
from ...models.candidate_level.resume_upload import Resume_upload
from ...models.candidate_level.resume_analysis import S_Resume_Analysis
from ...models.candidate_level.student_question import S_Question,generate_gemini_prompt_Question
from ..resume import generate_gemini_prompt


load_dotenv()
router = APIRouter()


def save_file(upload_file: UploadFile) -> str:
    if not upload_file:
        return None

    try:
        unique_filename = str(uuid.uuid4()) + "_" + upload_file.filename
        file_path = os.path.join("static","candidate_level", "resume_check", unique_filename)
        
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

# def generate_gemini_prompt(job_title: str, resume_text: str) -> str:
#     prompt = f"""
#     Evaluate the following resume against the provided job description and provide a detailed evaluation in a structured JSON format. Ensure that the JSON is valid and properly formatted, with all necessary commas included.

#     **Job Description:** {job_title}  
#     **Resume:** {resume_text}

#     1. Extract the **email** and **phone number** from the resume.
#     2. Include the contact information (email and phone number) in the JSON output.
#     3. The JSON should be properly formatted, valid, and include all required commas and syntax.

#     Please include the following keys in the JSON response:

#     {{
#         "overall_score": 0,
#         "resume_score": 0,
#         "resume_recommendations": [],
#         "candidate_name": "",
#         "candidate_email": "",
#         "candidate_phone": "",
#         "strengths": [],
#         "weaknesses": [],
#         "overall_suggestion": []
#     }}

#     ### Example Output:

#     {{
#         "overall_score": 85,
#         "resume_score": 78,
#         "resume_recommendations": [
#             "Strong action verbs used",
#             "Clearly defined skills section",
#             "Good use of quantifiable results"
#         ],
#         "resume_missing_elements": [
#             "Could benefit from a more impactful summary statement",
#             "Consider adding relevant certifications"
#         ],
#         "candidate_name": "John Doe",
#         "candidate_email": "john.doe@example.com",
#         "candidate_phone": "555-555-5555",
#         "strengths": ["Strong technical skills",
#           "Excellent communication", 
#           "Proven team player"],
#         "weaknesses": [
#             "Time management (working on it)",
#             "Public speaking (seeking opportunities to improve)"
#         ],
#         "overall_suggestion": [
#             "Consider adding a more impactful summary statement",
#             "Consider adding relevant certifications"
#         ],
#         "candidate_info": {{
#             "name": "John Doe",
#             "email": "candidate@example.com",
#             "phone": "+1234567890"
#             }}
#     }}

#     Return the response as valid JSON format with proper commas and no syntax errors.
#     """
#     return prompt

# generation_config={
#   "type": "object",
#   "properties": {
#     "overall_score": {
#       "type": "integer"
#     },
#     "resume_score": {
#       "type": "integer"
#     },
#     "resume_recommendations": {
#       "type": "array",
#       "items": {
#         "type": "string"
#       }
#     },
#     "candidate_name": {
#       "type": "string"
#     },
#     "candidate_email": {
#       "type": "string"
#     },
#     "candidate_phone": {
#       "type": "number"
#     },
#     "strengths": {
#       "type": "array",
#       "items": {
#         "type": "string"
#       }
#     },
#     "weaknesses": {
#       "type": "array",
#       "items": {
#         "type": "string"
#       }
#     },
#     "overall_suggestion": {
#       "type": "array",
#       "items": {
#         "type": "string"
#       }
#     }
#   },
#   "required": [
#     "overall_score",
#     "resume_score",
#     "resume_recommendations",
#     "candidate_name",
#     "candidate_email",
#     "candidate_phone",
#     "strengths",
#     "weaknesses",
#     "overall_suggestion"
#   ]
# }

@router.post("/resume_upload/candidate_level/")
async def upload_files(
    job_title: str = Form(...),
    upload_resumes: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: AI_Interviewer = Depends(get_current_user)
):
    try:
        candidate_db = db.query(AI_Interviewer).filter(AI_Interviewer.user_id == current_user.user_id).first()
        if not candidate_db:
            raise HTTPException(status_code=404, detail="User not found")
        
        candidate_resume = db.query(Resume_upload).filter(Resume_upload.user_id == current_user.user_id).first()
        resume_upload_count = candidate_resume.resume_upload_count if candidate_resume else 0

        if resume_upload_count >= 2:
            raise HTTPException(status_code=403, detail="You have already uploaded 2 resumes. Please subscribe for further uploads.")
        
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
        resume_score = cleaned_response.get("resume_score")
        resume_recommendations = cleaned_response.get("resume_recommendations")
        resume_missing_elements = cleaned_response.get("resume_missing_elements")
        candidate_info = cleaned_response.get("candidate_info")
        if candidate_info:
            name = candidate_info.get("name")
            email = candidate_info.get("email")
            phone = candidate_info.get("phone")
        overall_score = cleaned_response.get("overall_score")
        overall_suggestion = cleaned_response.get("overall_suggestion")
        strengths = cleaned_response.get("strengths")
        weaknesses = cleaned_response.get("weaknesses")

        resume_upload_count += 1  

        utc_now = pytz.utc.localize(datetime.utcnow())
        ist_now = utc_now.astimezone(pytz.timezone('Asia/Kolkata'))

        if candidate_resume:
            candidate_resume.file_path = file_path
            candidate_resume.resume_extract_data = resume_text.replace("```json", "").replace("\n", "").replace("```", "").replace("\\n", "").strip()
            candidate_resume.result = cleaned_response
            candidate_resume.resume_upload_count = resume_upload_count
            candidate_resume.uploaded_at = ist_now
        else:
            candidate_resume = Resume_upload(
                user_id=current_user.user_id,
                file_path=file_path,
                resume_extract_data=resume_text.replace("```json", "").replace("\n", "").replace("```", "").replace("\\n", "").strip(),
                result=cleaned_response,
                resume_upload_count=resume_upload_count,
                uploaded_at=ist_now,
            )
            db.add(candidate_resume)
            db.flush()

        resume_analysis_db = db.query(S_Resume_Analysis).filter(S_Resume_Analysis.resume_id == candidate_resume.id).first()
        if resume_analysis_db:
            resume_analysis_db.job_title = job_title
            resume_analysis_db.resume_score = resume_score
            resume_analysis_db.resume_recommendations = resume_recommendations
            resume_analysis_db.resume_missing_elements = resume_missing_elements
            resume_analysis_db.candidate_name = name
            resume_analysis_db.candidate_email = email
            resume_analysis_db.candidate_phone = phone
            resume_analysis_db.strengths = strengths
            resume_analysis_db.weaknesses = weaknesses
            resume_analysis_db.overall_score = overall_score
            resume_analysis_db.overall_suggestion = overall_suggestion
            resume_analysis_db.uploaded_at = ist_now
        else:
            resume_analysis_db = S_Resume_Analysis(
                resume_id=candidate_resume.id,
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

        question_entry = db.query(S_Question).filter(S_Question.resume_id == candidate_resume.id).first()
        if not question_entry:
            question_prompt = generate_gemini_prompt_Question(job_title)
            question_response = model.generate_content(question_prompt)
            gemini_question = clean_and_load_json(question_response.text)

            question_entry = S_Question(
                resume_id=candidate_resume.id,
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

        data = {
            "resume_id": candidate_resume.id,
            "user_id": candidate_resume.user_id,
            "resume_file_path": candidate_resume.file_path,
            "student_resume_result": {
                "name": name,
                "email": email,
                "phone": phone,
                "overall_score": overall_score,
                "strengths": strengths,
                "weaknesses": weaknesses,
                "resume_recommendations": resume_recommendations,
                "resume_missing_elements": resume_missing_elements,
                "overall_suggestion": overall_suggestion
            },
            "questions": {
                "Qustion1": question_entry.Qustion1,
                "Qustion2": question_entry.Qustion2,
                "Qustion3": question_entry.Qustion3,
                "Qustion4": question_entry.Qustion4,
                "Qustion5": question_entry.Qustion5
            }
        }

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        raise HTTPException(status_code=404, detail=f"{e}")      

    return data

@router.get("/candidate_level_resume_analysis/", response_model=None)
async def get_uploaded_resumes(
    db: Session = Depends(get_db),
    current_user: AI_Interviewer = Depends(get_current_user)
):
    try:
        resumes = db.query(Resume_upload).filter(Resume_upload.user_id == current_user.user_id).all()
        
        if not resumes:
            raise HTTPException(status_code=404, detail="No resumes found for this user.")

        response_data = []
        for resume in resumes:
            analysis = db.query(S_Resume_Analysis).filter(S_Resume_Analysis.resume_id == resume.id).first()
            questions = db.query(S_Question).filter(S_Question.resume_id == resume.id).first()

            resume_data = {
                "resume_id": resume.id,
                "user_id": resume.user_id,
                "file_path": resume.file_path,
                "resume_upload_count": resume.resume_upload_count,
                "uploaded_at": resume.uploaded_at,
                "resume_extract_data": resume.resume_extract_data,
                "result": resume.result,
                "resume_analysis": {
                    "job_title": analysis.job_title if analysis else None,
                    "resume_score": analysis.resume_score if analysis else None,
                    "resume_recommendations": analysis.resume_recommendations if analysis else None,
                    "resume_missing_elements": analysis.resume_missing_elements if analysis else None,
                    "candidate_name": analysis.candidate_name if analysis else None,
                    "candidate_email": analysis.candidate_email if analysis else None,
                    "candidate_phone": analysis.candidate_phone if analysis else None,
                    "strengths": analysis.strengths if analysis else None,
                    "weaknesses": analysis.weaknesses if analysis else None,
                    "overall_score": analysis.overall_score if analysis else None,
                    "overall_suggestion": analysis.overall_suggestion if analysis else None,
                } if analysis else None,
                "questions": {
                    "Qustion1": questions.Qustion1 if questions else None,
                    "Qustion2": questions.Qustion2 if questions else None,
                    "Qustion3": questions.Qustion3 if questions else None,
                    "Qustion4": questions.Qustion4 if questions else None,
                    "Qustion5": questions.Qustion5 if questions else None,
                } if questions else None
            }
            response_data.append(resume_data)

        return response_data
    
    except HTTPException as http_exc:
        raise http_exc
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


