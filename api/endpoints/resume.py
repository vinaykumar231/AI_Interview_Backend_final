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
import logging
import pytesseract
from pdf2image import convert_from_path
from .ocr_format import structure_ocr_data
import re


load_dotenv()

router = APIRouter()


def save_file(upload_file: UploadFile) -> str:
    if not upload_file:
        return None

    try:
        unique_filename = str(uuid.uuid4()) + "_" + upload_file.filename
        file_path = os.path.join("static", "uploads", unique_filename)
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)

        return file_path.replace("\\", "/")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
    
##################################
def extract_skills(resume_text):
    """
    Extracts skills from the resume text.
    """
    skills = []
    skills_match = re.search(r"SKILLS\s*=\s*{(.*?)}", resume_text, re.S)
    if skills_match:
        skills_text = skills_match.group(1)
        skills_pattern = re.compile(r'"([^"]+)":?\s*([\d\.]*)')
        skills = [match.group(1) for match in skills_pattern.finditer(skills_text)]
    return skills

def extract_experience(resume_text):
    """
    Extracts experience from the resume text.
    """
    experience = []
    
    # Adjust regex to match the expected format more reliably
    experience_match = re.search(r"EXPERIENCE\s*=\s*\[(.*?)\]", resume_text, re.S)
    if experience_match:
        experience_text = experience_match.group(1).strip()
        # Find all job entries
        experience_entries = re.findall(
            r"Job\(\s*start=\"(.*?)\",\s*end=\"?(.*?)\"?,\s*position=\"(.*?)\",\s*place=\"(.*?)\",\s*achievements=\[(.*?)\]", 
            experience_text, re.S
        )
        
        # Debug output to see if we are capturing entries
        print("Extracted Experience Entries:", experience_entries)  # Debug line

        for entry in experience_entries:
            achievements = re.findall(r'"(.*?)"', entry[4])  # Extract achievements
            experience.append({
                "start": entry[0],
                "end": entry[1] if entry[1] else "Present",  # Default to "Present" if end is None
                "position": entry[2],
                "place": entry[3],
                "achievements": achievements
            })
    else:
        print("No experience section found.")  # Debug line if no experience found
        
    return experience


def extract_education(resume_text):
    """
    Extracts education from the resume text.
    """
    education = []
    education_match = re.search(r"EDUCATION\s*=\s*\[(.*?)\]", resume_text, re.S)
    if education_match:
        education_text = education_match.group(1)
        education_entries = re.findall(
            r"Study\(\"(.*?)\", \"(.*?)\", \"(.*?)\", \"(.*?)\"\)|Certification\(\"(.*?)\"\)", 
            education_text, re.S
        )
        for entry in education_entries:
            if entry[0]:  # Study
                education.append({
                    "date": entry[0],
                    "institution": entry[1],
                    "field": entry[2],
                    "degree": entry[3]
                })
            elif entry[4]:  # Certification
                education.append({
                    "certification": entry[4]
                })
    return education


def extract_primary_data(resume_text):
    """
    Extracts primary data such as name, location, phone, email, and LinkedIn from the resume text.
    """
    primary_data = {
        "name": None,
        "location": None,
        "phone": None,
        "email": None,
        "linkedin": None,
    }
    
    # Extracting name (assuming the name is in the first line, before a slash)
    name_match = re.search(r"^\/([A-Z_]+)", resume_text)
    if name_match:
        primary_data["name"] = name_match.group(1).strip()
    
    # Extracting other primary data
    location_match = re.search(r'LOCATION\s*=\s*"([^"]+)"', resume_text)
    phone_match = re.search(r'PHONE\s*=\s*"([^"]+)"', resume_text)
    email_match = re.search(r'EMAIL\s*=\s*"([^"]+)"', resume_text)
    linkedin_match = re.search(r'LINKEDIN\s*=\s*"([^"]+)"', resume_text)
    
    if location_match:
        primary_data["location"] = location_match.group(1).strip()
    if phone_match:
        primary_data["phone"] = phone_match.group(1).strip()
    if email_match:
        primary_data["email"] = email_match.group(1).strip()
    if linkedin_match:
        primary_data["linkedin"] = linkedin_match.group(1).strip()
    
    return primary_data


#################################
    
def clean_and_load_json(raw_response: str):
    cleaned_response = raw_response.replace("```", "").replace("json", "").replace("\\n", "").strip()
    try:
        data = json.loads(cleaned_response)

        return data
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=404, detail="Json not read correct. Please try again.")
    

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
Here’s the modified prompt with an example output included:

---
**Modified Prompt:**

Evaluate the following resume against the provided job description and provide a detailed evaluation in a structured JSON format. Ensure that the JSON is valid and properly formatted, with all necessary commas included.

**Job Description:** {job_description}  
**Resume:** {resume_text}

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
}}

Return the response as valid JSON format with proper commas and no syntax errors. 
"""
    return prompt


@router.post("/upload/")
async def upload_file(
    job_title: str = Form(...),
    job_description: str = Form(...),
    upload_resume: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: AI_Interviewer = Depends(get_current_user)
):
    file_path = None
    try:
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

        genai.configure(api_key="AIzaSyCJyQo4J3-Xa9vpqjzMt6bmtJzxIGEOOjY")
        
        prompt = generate_gemini_prompt(job_description, resume_text)
        
        model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
        response = model.generate_content(prompt)
        gemini_evaluation = response.text

        cleaned_response = clean_and_load_json(gemini_evaluation)

        overall_score = cleaned_response.get("overall_score")
        relevance_score = cleaned_response.get("relevance")
        strengths=cleaned_response.get("strengths")
        skills_fit_score = cleaned_response.get("skills_fit")
        weaknesses=cleaned_response.get("weaknesses")
        cultural_fit_score = cleaned_response.get("cultural_fit")
        recommendations=cleaned_response.get("recommendations")
        experience_match_score = cleaned_response.get("experience_match")
        missing_elements=cleaned_response.get("missing_elements")

        # after OCR grt deatils in orgnized formatd means json
        primary_data = extract_primary_data(resume_text)
        skills = extract_skills(resume_text)
        experience = extract_experience(resume_text)
        education = extract_education(resume_text)
        
        company = db.query(Companies).filter(Companies.hr_id == current_user.user_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="No company found for the current user")
        
        utc_now = pytz.utc.localize(datetime.utcnow())
        ist_now = utc_now.astimezone(pytz.timezone('Asia/Kolkata'))

        resume_entry = Resume(
            company_id=company.id,
            user_id=current_user.user_id,
            file_path=file_path,
            resume_extract_data=resume_text.replace("```json", "").replace("\n", "").replace("```", "").replace("\\n", "").strip(),
            result=cleaned_response,
            uploaded_at=ist_now,
        )
        db.add(resume_entry)
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

        return {
            "resume_id":resume_entry.id,
            "filename": upload_resume.filename,
            "company_id": resume_entry.company_id,
            "hr_id":resume_entry.user_id,
            "resume_file_path": resume_entry.file_path,
             "resume_extract_details": {
                "resume_details":resume_text,
                "primary_data": primary_data,
                "skills": skills,
                "experience": experience,
                "education": education,
            },
            "job_description": {
                "job_title": job_description_db.job_title,
                "job_description": job_description_db.job_description,
            },
            "resume_selection_result":{
                "overall_score" :overall_score,
                "relevance_score" :relevance_score,
                "cultural_fit_score" :cultural_fit_score,
                "skills_fit_score" :skills_fit_score,
                "experience_match_score" :experience_match_score,
                "strengths":strengths,
                "weaknesses":weaknesses,
                "recommendations":recommendations,
                "missing_elements":missing_elements,

            },
          
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
           

@router.get("/resumes/{resume_id}", response_model=ResumeCreate)
def get_resume(resume_id: int, db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume

@router.put("/resumes/{resume_id}", response_model=ResumeUpdate)
def update_resume_status(resume_id: int, status: str, db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    resume.status = status
    db.commit()
    db.refresh(resume)
    return resume

@router.delete("/resumes/{resume_id}")
def delete_resume(resume_id: int, db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    db.delete(resume)
    db.commit()
    return {"message": "Resume deleted successfully"}
