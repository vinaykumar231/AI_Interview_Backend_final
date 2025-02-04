import shutil
from fastapi import APIRouter, File, HTTPException, Depends, Form, UploadFile
from sqlalchemy.orm import Session

from api.endpoints.resume import extract_text_from_docx, extract_text_from_pdf, extract_text_with_ocr, save_file
from auth.auth_bearer import get_current_user
from ..models.resume import Resume
from database import get_db
from ..schemas import ResumeCreate, ResumeUpdate
import json
import os
import uuid
import google.generativeai as genai
from pydantic import BaseModel
import pytz
from datetime import datetime
from dotenv import load_dotenv
from ..models.job_description import Job_Descriptions
from ..models.user import AI_Interviewer
from ..models.company import Companies
from ..models.resume_analysis import Resume_Analysis
from ..models.question import generate_gemini_prompt_Question, Question
from ..models.interview_scheduled_data import InterviewScheduledData

load_dotenv()
router = APIRouter()

def clean_and_load_json(raw_response: str):
    cleaned_response = raw_response.replace("```", "").replace("json", "").replace("\\n", "").strip()
    try:
        data = json.loads(cleaned_response)
        return data
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=404, detail="Due to Technical Error file not read correctly. Please try again.")

def generate_gemini_prompt(job_description: str, resume_text: str) -> str:
    prompt = f"""
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
        "recommendations": <list of suggestions for improvement>,
        "candidate_info": {{
            "name": "John Doe",
            "email": "candidate@example.com",
            "phone": "+1234567890"
        }}
    }}
    """
    return prompt

@router.post("/job_apply_resume_analysis/")
async def upload_files(
    candidate_data: str = Form(...),
    job_description: str = Form(...),
    hr_id :int =Form(...),
    db: Session = Depends(get_db),
   
):
    results = []
    try:
        
        job_description_dict = json.loads(job_description)
        job_title = job_description_dict.get("job_title")

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid job description format")

    try:
        user= db.query(AI_Interviewer).filter(AI_Interviewer.user_id==hr_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="HR not found")
        
        genai.configure(api_key=os.environ["API_KEY_gm"])
        prompt = generate_gemini_prompt(job_description, candidate_data)
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

        company = db.query(Companies).filter(Companies.hr_id == user.user_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="No company found for the current user")

        utc_now = pytz.utc.localize(datetime.utcnow())
        ist_now = utc_now.astimezone(pytz.timezone('Asia/Kolkata'))

        resume_entry = Resume(
            company_id=company.id,
            job_title=job_title,
            user_id=user.user_id,
            candidate_email=email,
            resume_extract_data=candidate_data.strip(),
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
            hr_id=user.user_id,
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
            user_id=user.user_id,
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
            "company_id": resume_entry.company_id,
            "hr_id": resume_entry.user_id,
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


####################################################


# @router.post("/resume_uploadfor_job_apply/")
# async def upload_files(
#     candidate_file: UploadFile = File(...),
#     job_description_file: UploadFile = File(...),
#     db: Session = Depends(get_db),
#     current_user: AI_Interviewer = Depends(get_current_user)
# ):
#     results = []
#     try:
#         # Save the uploaded files
#         candidate_file_path = save_file(candidate_file)
#         job_description_file_path = save_file(job_description_file)

#         if not candidate_file_path or not os.path.isfile(candidate_file_path):
#             raise HTTPException(status_code=400, detail="Failed to save the uploaded resume file")

#         if not job_description_file_path or not os.path.isfile(job_description_file_path):
#             raise HTTPException(status_code=400, detail="Failed to save the uploaded job description file")

#         # Check file sizes
#         candidate_file_size = os.path.getsize(candidate_file_path)
#         if candidate_file_size == 0:
#             raise HTTPException(status_code=400, detail="The uploaded resume file is empty")

#         job_description_file_size = os.path.getsize(job_description_file_path)
#         if job_description_file_size == 0:
#             raise HTTPException(status_code=400, detail="The uploaded job description file is empty")

#         # Extract text from files
#         if candidate_file_path.lower().endswith(".pdf"):
#             resume_text = extract_text_from_pdf(candidate_file_path)
#             if not resume_text.strip():
#                 resume_text = extract_text_with_ocr(candidate_file_path)
#         elif candidate_file_path.lower().endswith(".docx"):
#             resume_text = extract_text_from_docx(candidate_file_path)
#         else:
#             raise HTTPException(status_code=400, detail="Unsupported resume file type")

#         if not resume_text.strip():
#             resume_text = "No readable text could be extracted from this file."

#         job_description_text = ""
#         if job_description_file_path.lower().endswith(".pdf"):
#             job_description_text = extract_text_from_pdf(job_description_file_path)
#         elif job_description_file_path.lower().endswith(".docx"):
#             job_description_text = extract_text_from_docx(job_description_file_path)
#         else:
#             raise HTTPException(status_code=400, detail="Unsupported job description file type")

#         if not job_description_text.strip():
#             job_description_text = "No readable text could be extracted from the job description."

#         # Configure AI Model
#         genai.configure(api_key=os.environ["API_KEY_gm"])
#         prompt = generate_gemini_prompt(job_description_text, resume_text)
#         model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
#         response = model.generate_content(prompt)
#         gemini_evaluation = response.text

#         cleaned_response = clean_and_load_json(gemini_evaluation)

#         # Extract candidate info
#         candidate_info = cleaned_response.get("candidate_info")
#         if candidate_info:
#             name = candidate_info.get("name")
#             email = candidate_info.get("email")
#             phone = candidate_info.get("phone")

#         # Extract additional data
#         overall_score = cleaned_response.get("overall_score")
#         relevance_score = cleaned_response.get("relevance")
#         strengths = cleaned_response.get("strengths")
#         skills_fit_score = cleaned_response.get("skills_fit")
#         weaknesses = cleaned_response.get("weaknesses")
#         cultural_fit_score = cleaned_response.get("cultural_fit")
#         recommendations = cleaned_response.get("recommendations")
#         experience_match_score = cleaned_response.get("experience_match")
#         missing_elements = cleaned_response.get("missing_elements")

#         # Get company info from the database
#         company = db.query(Companies).filter(Companies.hr_id == current_user.user_id).first()
#         if not company:
#             raise HTTPException(status_code=404, detail="No company found for the current user")

#         # Get current time in IST
#         utc_now = pytz.utc.localize(datetime.utcnow())
#         ist_now = utc_now.astimezone(pytz.timezone('Asia/Kolkata'))

#         # Save resume data to database
#         resume_entry = Resume(
#             company_id=company.id,
#             user_id=current_user.user_id,
#             candidate_email=email,
#             file_path=candidate_file_path,
#             resume_extract_data=resume_text.replace("```json", "").replace("\n", "").replace("```", "").replace("\\n", "").strip(),
#             result=cleaned_response,
#             uploaded_at=ist_now,
#         )
#         db.add(resume_entry)
#         db.flush()

#         # Determine resume selection status
#         SCORE_THRESHOLD = int(os.getenv('SCORE_THRESHOLD', 75))
#         RESUME_SELECTED_MESSAGE = os.getenv('RESUME_SELECTED_MESSAGE', 'resume selected')
#         RESUME_REJECTED_MESSAGE = os.getenv('RESUME_REJECTED_MESSAGE', 'resume rejected')

#         resume_status = RESUME_SELECTED_MESSAGE if overall_score >= SCORE_THRESHOLD else RESUME_REJECTED_MESSAGE

#         # Save resume analysis data to database
#         resume_analysis_db = Resume_Analysis(
#             resume_id=resume_entry.id,
#             hr_id=current_user.user_id,
#             candidate_name=name,
#             candidate_email=email,
#             candidate_phone=phone,
#             overall_score=overall_score,
#             relevance_score=relevance_score,
#             experience_match_score=experience_match_score,
#             cultural_fit_score=cultural_fit_score,
#             strengths=strengths,
#             weaknesses=weaknesses,
#             recommendations=recommendations,
#             missing_elements=missing_elements,
#             uploaded_at=ist_now,
#             resume_selection_status=resume_status,
#         )
#         db.add(resume_analysis_db)
#         db.flush()

#         # Save job description to database
#         job_description_db = Job_Descriptions(
#             company_id=company.id,
#             user_id=current_user.user_id,
#             job_description=job_description_text,
#             created_on=ist_now,
#         )
#         db.add(job_description_db)
#         db.commit()

#         # If resume is selected, generate interview questions
#         if resume_status == 'resume selected':
#             question_prompt = generate_gemini_prompt_Question(job_description_text)
#             question_response = model.generate_content(question_prompt)
#             gemini_question = clean_and_load_json(question_response.text)

#             question_entry = Question(
#                 resume_id=resume_entry.id,
#                 candidate_name=name,
#                 candidate_email=email,
#                 resume_selection_status=resume_status,
#                 Qustion1=gemini_question.get('experience_based_questions', [None])[0],
#                 Qustion2=gemini_question.get('experience_based_questions', [None])[1],
#                 Qustion3=gemini_question.get('behavioral_questions', [None])[0],
#                 Qustion4=gemini_question.get('behavioral_questions', [None])[1],
#                 Qustion5=gemini_question.get('cultural_fit_and_career_development_questions', [None])[0],
#                 is_ai_generated=True,
#                 created_on=ist_now,
#             )
#             db.add(question_entry)
#             db.commit()

#         results.append({
#             "resume_id": resume_entry.id,
#             "name": name,
#             "filename": candidate_file.filename,
#             "company_id": resume_entry.company_id,
#             "hr_id": resume_entry.user_id,
#             "resume_file_path": resume_entry.file_path,
#             "job_description": {
#                 "job_title": job_description_db.job_title,
#                 "job_description": job_description_db.job_description,
#             },
#             "resume_selection_result": {
#                 "candidate_info": {
#                     "name": name,
#                     "email": email,
#                     "phone": phone,
#                 },
#                 "questions": {
#                     "generated_questions": {
#                         "resume_id": resume_entry.id,
#                         "resume_selection_status": resume_status,
#                         "all_questions": {
#                             "Qustion1": question_entry.Qustion1,
#                             "Qustion2": question_entry.Qustion2,
#                             "Qustion3": question_entry.Qustion3,
#                             "Qustion4": question_entry.Qustion4,
#                             "Qustion5": question_entry.Qustion5,
#                         } if resume_status == 'resume selected' else None,
#                     },
#                 },
#                 "overall_score": overall_score,
#                 "relevance_score": relevance_score,
#                 "cultural_fit_score": cultural_fit_score,
#                 "skills_fit_score": skills_fit_score,
#                 "experience_match_score": experience_match_score,
#                 "strengths": strengths,
#                 "weaknesses": weaknesses,
#                 "recommendations": recommendations,
#                 "missing_elements": missing_elements,
#                 "resume_selection_status": resume_status,
#             },
#         })

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    
#     return results

##########################################################

# def generate_gemini_prompt(resume_text: str) -> str:
#     prompt = f"""
#     Evaluate the following resume and provide a detailed evaluation in a structured JSON format. Ensure that the JSON is valid and properly formatted, with all necessary commas included.
#     **Resume:** {resume_text}
    
#     1. Extract the **email** and **phone number** from the resume.
#     2. Include the contact information (email and phone number) in the JSON output.
#     3. The JSON should be properly formatted, valid, and include all required commas and syntax.

#     Please include the following keys in the JSON response:
#     {{
#         "overall_score": <numeric value between 0 and 100>,
#         "relevance": <numeric score between 0 and 10>,
#         "skills_fit": <numeric score between 0 and 10>,
#         "experience_match": <numeric score between 0 and 10>,
#         "cultural_fit": <numeric score between 0 and 10>,
#         "strengths": <list of key strengths>,
#         "weaknesses": <list of key weaknesses or gaps>,
#         "missing_elements": <list of key missing qualifications or experiences>,
#         "recommendations": <list of suggestions for improvement>,
#         "candidate_info": {{
#             "email": "candidate@example.com",
#             "phone": "+1234567890"
#         }}
#     }}
#     """
#     return prompt


# @router.post("/job_apply_resume_analysis_only_data/")
# async def upload_files(
#     data: str = Form(...),  # Assuming only resume data is passed
#     db: Session = Depends(get_db),
#     current_user: AI_Interviewer = Depends(get_current_user)
# ):
#     results = []
#     try:
#         genai.configure(api_key=os.environ["API_KEY_gm"])

#         # Use only the resume data for analysis (no job description or candidate data)
#         prompt = generate_gemini_prompt(data)  # Modify the prompt to only consider resume data
#         model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
#         response = model.generate_content(prompt)
#         gemini_evaluation = response.text

#         cleaned_response = clean_and_load_json(gemini_evaluation)

#         candidate_info = cleaned_response.get("candidate_info")
#         if candidate_info:
#             name = candidate_info.get("name")
#             email = candidate_info.get("email")
#             phone = candidate_info.get("phone")

#         overall_score = cleaned_response.get("overall_score")
#         relevance_score = cleaned_response.get("relevance")
#         strengths = cleaned_response.get("strengths")
#         skills_fit_score = cleaned_response.get("skills_fit")
#         weaknesses = cleaned_response.get("weaknesses")
#         cultural_fit_score = cleaned_response.get("cultural_fit")
#         recommendations = cleaned_response.get("recommendations")
#         experience_match_score = cleaned_response.get("experience_match")
#         missing_elements = cleaned_response.get("missing_elements")

#         company = db.query(Companies).filter(Companies.hr_id == current_user.user_id).first()
#         if not company:
#             raise HTTPException(status_code=404, detail="No company found for the current user")

#         utc_now = pytz.utc.localize(datetime.utcnow())
#         ist_now = utc_now.astimezone(pytz.timezone('Asia/Kolkata'))

#         resume_entry = Resume(
#             company_id=company.id,
#             user_id=current_user.user_id,
#             candidate_email=email,
#             result=cleaned_response,
#             uploaded_at=ist_now,
#         )
#         db.add(resume_entry)
#         db.flush()

#         SCORE_THRESHOLD = int(os.getenv('SCORE_THRESHOLD', 75))
#         RESUME_SELECTED_MESSAGE = os.getenv('RESUME_SELECTED_MESSAGE', 'resume selected')
#         RESUME_REJECTED_MESSAGE = os.getenv('RESUME_REJECTED_MESSAGE', 'resume rejected')

#         resume_status = RESUME_SELECTED_MESSAGE if overall_score >= SCORE_THRESHOLD else RESUME_REJECTED_MESSAGE

#         resume_analysis_db = Resume_Analysis(
#             resume_id=resume_entry.id,
#             hr_id=current_user.user_id,
#             candidate_name=name,
#             candidate_email=email,
#             candidate_phone=phone,
#             overall_score=overall_score,
#             relevance_score=relevance_score,
#             experience_match_score=experience_match_score,
#             cultural_fit_score=cultural_fit_score,
#             strengths=strengths,
#             weaknesses=weaknesses,
#             recommendations=recommendations,
#             missing_elements=missing_elements,
#             uploaded_at=ist_now,
#             resume_selection_status=resume_status,
#         )
#         db.add(resume_analysis_db)
#         db.flush()

#         job_description_db = Job_Descriptions(
#             company_id=company.id,
#             user_id=current_user.user_id,
#             job_title="Job Title Placeholder",  # No job description needed
#             job_description="Job Description Placeholder",  # No job description needed
#             created_on=ist_now,
#         )
#         db.add(job_description_db)
#         db.commit()

#         if resume_status == 'resume selected':
#             question_prompt = generate_gemini_prompt_Question(data)  # Placeholder job title
#             question_response = model.generate_content(question_prompt)
#             gemini_question = clean_and_load_json(question_response.text)

#             question_entry = Question(
#                 resume_id=resume_entry.id,
#                 candidate_name=name,
#                 candidate_email=email,
#                 resume_selection_status=resume_status,
#                 Qustion1=gemini_question.get('experience_based_questions', [None])[0],
#                 Qustion2=gemini_question.get('experience_based_questions', [None])[1],
#                 Qustion3=gemini_question.get('behavioral_questions', [None])[0],
#                 Qustion4=gemini_question.get('behavioral_questions', [None])[1],
#                 Qustion5=gemini_question.get('cultural_fit_and_career_development_questions', [None])[0],
#                 is_ai_generated=True,
#                 created_on=ist_now,
#             )
#             db.add(question_entry)
#             db.commit()

#         results.append({
#             "resume_id": resume_entry.id,
#             "name": name,
#             "company_id": resume_entry.company_id,
#             "hr_id": resume_entry.user_id,
#             "resume_selection_result": {
#                 "candidate_info": {
#                     "name": name,
#                     "email": email,
#                     "phone": phone,
#                 },
#                 "questions": {
#                     "generated_questions": {
#                         "resume_id": resume_entry.id,
#                         "resume_selection_status": resume_status,
#                         "all_questions": {
#                             "Qustion1": question_entry.Qustion1,
#                             "Qustion2": question_entry.Qustion2,
#                             "Qustion3": question_entry.Qustion3,
#                             "Qustion4": question_entry.Qustion4,
#                             "Qustion5": question_entry.Qustion5,
#                         } if resume_status == 'resume selected' else None,
#                     },
#                 },
#                 "overall_score": overall_score,
#                 "relevance_score": relevance_score,
#                 "cultural_fit_score": cultural_fit_score,
#                 "skills_fit_score": skills_fit_score,
#                 "experience_match_score": experience_match_score,
#                 "strengths": strengths,
#                 "weaknesses": weaknesses,
#                 "recommendations": recommendations,
#                 "missing_elements": missing_elements,
#                 "resume_selection_status": resume_status,
#             },
#         })

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    
#     return results
