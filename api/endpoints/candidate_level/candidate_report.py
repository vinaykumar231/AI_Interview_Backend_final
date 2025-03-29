import re
from fastapi import APIRouter, File, UploadFile, HTTPException,Form,Depends
from datetime import datetime
import pytz
import os
import json
import time
import glob
import sqlite3
import ffmpeg
import tempfile
import google.generativeai as genai
from sqlalchemy import desc, func
from api.endpoints.report import configure_gemini_model, save_upload_file_video
from api.models.report import Report
from api.models.user import AI_Interviewer
from auth.auth_bearer import get_current_user
from generate_pdf_report import generate_pdf
from datetime import datetime
import subprocess
import uuid
import shutil
from sqlalchemy.orm import Session
from database import get_db
from ...models.candidate_level.report import Candidate_Report,save_upload_resume
from ...models.candidate_level.video import S_Video
from typing import Optional
from ...models.candidate_level.student_question import S_Question
import logging
from ..report import  system_prompt, generate_gemini_prompt_for_report_generate


router = APIRouter()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

    
############################################  For Report generate  #######################################################

UPLOAD_DIR2 = os.path.join(os.getcwd(), 'static',"candidate_level", 'final_report')
if not os.path.exists(UPLOAD_DIR2):
    os.mkdir(UPLOAD_DIR2)

def save_upload_file_video(upload_file: UploadFile) :
    if not upload_file:
        return None
    
    try:
        unique_filename = str(uuid.uuid4()) + "_" + upload_file.filename
        file_path = os.path.join("static","candidate_level", "videos", unique_filename)
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
        
        file_path = file_path.replace("\\", "/")
        return file_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
    


@router.post("/candidaate/analyze/")
async def analyze_video(
    email: str = Form(...),
    resume: UploadFile = File(...),
    video: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: AI_Interviewer = Depends(get_current_user)
):
    video_url = None
    resume_url = None
    interview_done_count=0

    try:
        candidate = db.query(Candidate_Report).filter(Candidate_Report.user_id ==current_user.user_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not candidate:
            interview_done_count = 0  
        else:
            interview_done_count = candidate.interview_done_count

        if interview_done_count >= 2:
            raise HTTPException(status_code=403, detail="You have already attended 2 interviews. To continue, please subscribe for further interviews.")
        
        logger.info(f"Processing video analysis for email: {email}")

        resume_url = save_upload_resume(resume)
        video_url = save_upload_file_video(video)
        logger.info(f"Video saved at: {video_url}")

        logger.info("Uploading video to Gemini API")
        video_file = genai.upload_file(video_url)

        max_retries = 30
        retry_count = 0
        while video_file.state.name == "PROCESSING" and retry_count < max_retries:
            time.sleep(10)
            video_file = genai.get_file(video_file.name)
            retry_count += 1
            logger.info(f"Waiting for video processing... Attempt {retry_count}/{max_retries}")

        if video_file.state.name == "FAILED" or retry_count >= max_retries:
            raise HTTPException(
                status_code=500,
                detail="Failed to process video or processing timeout."
            )

        logger.info("Retrieving latest questions from database")

        subquery = (
            db.query(
                S_Question.candidate_email,
                func.max(S_Question.created_on).label("latest_questions_date")
            )
            .group_by(S_Question.candidate_email)
            .subquery()
        )

        question_db = (
            db.query(S_Question)
            .join(
                subquery,
                (S_Question.candidate_email == subquery.c.candidate_email) &
                (S_Question.created_on == subquery.c.latest_questions_date)
            )
            .filter(S_Question.candidate_email == email)
            .first()
        )

        if not question_db:
            raise HTTPException(status_code=404, detail="No questions found for the given email.")

        questions = {
            'question1': question_db.Qustion1,
            'question2': question_db.Qustion2,
            'question3': question_db.Qustion3,
            'question4': question_db.Qustion4,
            'question5': question_db.Qustion5
        }
        logger.info(f"Retrieved questions: {questions}")

        generation_config = configure_gemini_model()
        logger.info("Generating content with Gemini API")

        try:
            model = genai.GenerativeModel(
                model_name="models/gemini-1.5-flash",
                generation_config=generation_config,
                system_instruction=system_prompt,
            )

            prompt = generate_gemini_prompt_for_report_generate(questions)

            response = model.generate_content(
                [video_file, prompt],
                request_options={"timeout": 600}
            )
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error generating content: {str(e)}")

        analysis_output = response.text.strip()
        logger.info(f"Raw API response received: {analysis_output[:200]}...")

        try:
            cleaned_output = analysis_output
            if "```json" in cleaned_output:
                cleaned_output = cleaned_output.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned_output:
                cleaned_output = cleaned_output.split("```")[1].split("```")[0].strip()

            cleaned_output = cleaned_output.replace("\n", " ").replace("    ", "").strip()
            cleaned_output = re.sub(r',(\s*[}\]])', r'\1', cleaned_output)

            analysis_data = json.loads(cleaned_output)
        except Exception as e:
            logger.error(f"JSON parsing error: {str(e)}")
            logger.error(f"Raw content causing error: {analysis_output}")

            analysis_data = {
                "analysis": {
                    "raw_text": analysis_output,
                    "timestamp": datetime.now().isoformat(),
                    "email": email
                }
            }

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_output_path = os.path.join('static', "candidate_level", 'final_report', f"{email}_analysis_{timestamp}.json").replace("\\", "/")
        pdf_file_path = os.path.join('static', "candidate_level", 'final_report', f"{email}_analysis_report_{timestamp}.pdf").replace("\\", "/")

        with open(json_output_path, 'w', encoding='utf-8') as json_output_file:
            json.dump(analysis_data, json_output_file, indent=4, ensure_ascii=False)

        generate_pdf(json_output_path, pdf_file_path)

        interview_done_count +=1

        utc_now = pytz.utc.localize(datetime.utcnow())
        ist_now = utc_now.astimezone(pytz.timezone('Asia/Kolkata'))
        if candidate:
            candidate.user_id=current_user.user_id,
            candidate.email=email,
            candidate.resume_file=resume_url,
            candidate.interview_done_count = interview_done_count,
            candidate.report_file_path = pdf_file_path
            candidate.video_url = video_url
            candidate.created_on=ist_now,
        else:
            candidate = Candidate_Report(
                user_id=current_user.user_id,
                resume_file=resume_url,
                email=email,
                report_file_path=pdf_file_path,
                video_url=video_url,
                interview_done_count = 1,
                created_on=ist_now,
            )
            db.add(candidate)
        db.commit()

        try:
            genai.delete_file(video_file.name)
        except Exception as e:
            logger.warning(f"Failed to delete Gemini video file: {str(e)}")

        return {
            "status": "success",
            "message": "Analysis complete",
            "report_path": pdf_file_path,
            "json_path": json_output_path,
            "questions": questions
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
