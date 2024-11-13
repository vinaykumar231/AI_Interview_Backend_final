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
from api.models.resume_analysis import Resume_Analysis
from api.models.user import AI_Interviewer
from auth.auth_bearer import get_current_user
from generate_pdf_report import generate_pdf
from datetime import datetime
import subprocess
import uuid
import shutil
from sqlalchemy.orm import Session
from database import get_db
from ..models.report import Report,save_upload_resume,generate_gemini_prompt_for_report_generate
from ..models.video import Video
from typing import Optional
from ..models.question import Question
import logging
import re
from sqlalchemy.orm import Session, joinedload
from dotenv import load_dotenv




load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
router = APIRouter()


def save_upload_file(upload_file: UploadFile) :
    if not upload_file:
        return None
    
    try:
        unique_filename = str(uuid.uuid4()) + "_" + upload_file.filename
        file_path = os.path.join("static", "videos", unique_filename)
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Open the file in binary write mode
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
        
        file_path = file_path.replace("\\", "/")
        return file_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")


@router.post("/upload_videos/")
async def upload_video(video: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        saved_file_path = save_upload_file(video)
        video_db = Video(
            file_path=saved_file_path,
        )
        db.add(video_db)
        db.commit()
        return {"message": "Video uploaded successfully", "video": video_db.file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
############################################  For Report generate  #######################################################



UPLOAD_DIR = os.path.join(os.getcwd(), 'static', 'merge_videos')
if not os.path.exists(UPLOAD_DIR):
    os.mkdir(UPLOAD_DIR)

VIDEOS_DIR1 = os.path.join(os.getcwd(), "static", "videos")
if not os.path.exists(VIDEOS_DIR1):
    os.mkdir(VIDEOS_DIR1)

UPLOAD_DIR2 = os.path.join(os.getcwd(), 'static', 'final_report')
if not os.path.exists(UPLOAD_DIR2):
    os.mkdir(UPLOAD_DIR2)

genai.configure(api_key=os.environ.get("API_KEY_gm", ""))

def concatenate_videos(video_files, output_file):
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as list_file:
        for file_path in video_files:
            list_file.write(f"file '{file_path}'\n")
        list_file_path = list_file.name

    try:
        command = [
            'ffmpeg', '-f', 'concat', '-safe', '0', '-i', list_file_path, '-c', 'copy', output_file
        ]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"ffmpeg error: {result.stderr}")

    finally:
        os.remove(list_file_path)  






def save_upload_file_video(upload_file: UploadFile) :
    if not upload_file:
        return None
    
    try:
        unique_filename = str(uuid.uuid4()) + "_" + upload_file.filename
        file_path = os.path.join("static", "videos", unique_filename)
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Open the file in binary write mode
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
        
        file_path = file_path.replace("\\", "/")
        return file_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")


@router.post("/upload_videos/")
async def upload_video(video: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        saved_file_path = save_upload_file(video)
        video_db = Video(
            file_path=saved_file_path,
        )
        db.add(video_db)
        db.commit()
        return {"message": "Video uploaded successfully", "video": video_db.file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
############################################  For Report generate  #######################################################



# UPLOAD_DIR = os.path.join(os.getcwd(), 'static', 'merge_videos')
# if not os.path.exists(UPLOAD_DIR):
#     os.mkdir(UPLOAD_DIR)

# VIDEOS_DIR1 = os.path.join(os.getcwd(), "static", "videos")
# if not os.path.exists(VIDEOS_DIR1):
#     os.mkdir(VIDEOS_DIR1)

UPLOAD_DIR2 = os.path.join(os.getcwd(), 'static', 'final_report')
if not os.path.exists(UPLOAD_DIR2):
    os.mkdir(UPLOAD_DIR2)

genai.configure(api_key=os.environ.get("API_KEY_gm", ""))

def concatenate_videos(video_files, output_file):
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as list_file:
        for file_path in video_files:
            list_file.write(f"file '{file_path}'\n")
        list_file_path = list_file.name

    try:
        command = [
            'ffmpeg', '-f', 'concat', '-safe', '0', '-i', list_file_path, '-c', 'copy', output_file
        ]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"ffmpeg error: {result.stderr}")

    finally:
        os.remove(list_file_path) 

# def save_upload_file_video_analyze(upload_file: UploadFile) -> str:
#     try:
#         unique_filename = str(uuid.uuid4()) + "_" + upload_file.filename
#         file_path = os.path.join('static', 'videos', unique_filename)
#         with open(file_path, "wb") as buffer:
#             shutil.copyfileobj(upload_file.file, buffer)
#         return file_path
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}") 

@router.post("/analyze")
async def analyze_video(
    email: str = Form(...),
    resume: UploadFile = File(...),
    video: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    video_url = None
    resume_url = None

    try:

        hr_db=db.query(Resume_Analysis).filter(Resume_Analysis.candidate_email==email).first()
        if not hr_db:
            raise HTTPException(status_code=404, detail="hr not found")
        
        logger.info(f"Processing video analysis for email: {email}")

        # Save uploaded files
        resume_url = save_upload_resume(resume)
        video_url = save_upload_file_video(video)
        print('video',video_url)
        
        # Upload to Gemini API
        logger.info("Uploading video to Gemini API")
        video_file = genai.upload_file(video_url)
        
        # Wait for video processing with timeout
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

        # Get questions from database
        logger.info("Retrieving questions from database")
        question_db = db.query(Question).filter(Question.candidate_email == email).all()

        if not question_db:
            raise HTTPException(status_code=404, detail="No questions found for the given email.")

        questions = {
            'question1': question_db[0].Qustion1,
            'question2': question_db[0].Qustion2,
            'question3': question_db[0].Qustion3,
            'question4': question_db[0].Qustion4,
            'question5': question_db[0].Qustion5
        }

        dynamic_question = generate_gemini_prompt_for_report_generate(**questions)

        # Generate content with error handling
        logger.info("Generating content with Gemini API")
        try:
            model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")
            response = model.generate_content(
                [video_file, dynamic_question],
                request_options={"timeout": 600}
            )
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error generating content: {str(e)}")

        # Process the response
        analysis_output = response.text.strip()
        logger.info(f"Raw API response received: {analysis_output[:200]}...")

        # Clean and parse JSON
        try:
            # Remove any potential markdown formatting
            cleaned_output = analysis_output
            if "```json" in cleaned_output:
                cleaned_output = cleaned_output.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned_output:
                cleaned_output = cleaned_output.split("```")[1].split("```")[0].strip()
            
            # Fix common JSON issues
            cleaned_output = cleaned_output.replace("\n", " ")
            cleaned_output = cleaned_output.replace("    ", "")
            cleaned_output = cleaned_output.strip()
            
            # Remove any trailing commas before closing braces/brackets
            cleaned_output = re.sub(r',(\s*[}\]])', r'\1', cleaned_output)
            
            # Parse the cleaned JSON
            analysis_data = json.loads(cleaned_output)
            
        except Exception as e:
            logger.error(f"JSON parsing error: {str(e)}")
            logger.error(f"Raw content causing error: {analysis_output}")
            
            # Attempt to salvage the JSON by creating a simpler structure
            try:
                # Create a basic structure with the raw text
                analysis_data = {
                    "analysis": {
                        "raw_text": analysis_output,
                        "timestamp": datetime.now().isoformat(),
                        "email": email
                    }
                }
            except Exception as inner_e:
                logger.error(f"Failed to create fallback JSON: {str(inner_e)}")
                raise HTTPException(
                    status_code=500,
                    detail="Failed to process analysis output"
                )

        # Define file paths for JSON and PDF
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_output_path = os.path.join("static", "final_report", f"{email}_analysis_{timestamp}.json").replace("\\", "/")
        pdf_file_path = os.path.join("static", "final_report", f"{email}_analysis_report_{timestamp}.pdf").replace("\\", "/")

        # Save JSON with proper encoding
        with open(json_output_path, 'w', encoding='utf-8') as json_output_file:
            json.dump(analysis_data, json_output_file, indent=4, ensure_ascii=False)

        # Generate PDF
        generate_pdf(json_output_path, pdf_file_path)

        # Save to database
        utc_now = pytz.utc.localize(datetime.utcnow())
        ist_now = utc_now.astimezone(pytz.timezone('Asia/Kolkata'))
        report_db = Report(
            hr_id=hr_db.hr_id,
            candidate_name=hr_db.candidate_name,
            resume_file=resume_url,
            email=email,
            report_file_path=pdf_file_path,
            video_url=video_url,
            created_on=ist_now,
        )
        db.add(report_db)
        db.commit()

        # Cleanup
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
    # finally:
    #     # Cleanup temporary files if needed
    #     for path in [video_url, resume_url]:
    #         try:
    #             if path and os.path.exists(path):
    #                 os.remove(path)
    #         except Exception as e:
    #             logger.warning(f"Failed to cleanup temporary file {path}: {str(e)}")

base_url_path = os.getenv("BASE_URL_PATH")

@router.get("/resume_report_pdf/", response_model=None)
def get_resume_reports(db: Session = Depends(get_db), current_user: AI_Interviewer = Depends(get_current_user)):
    try:
        selected_resumes = db.query(Report).filter(Report.hr_id == current_user.user_id).all()
        if not selected_resumes:
            raise HTTPException(status_code=404, detail="not found ")

        resume_list = []
        for resume in selected_resumes:
            report_url = f"{base_url_path}/{resume.report_file_path}"
            resume_url = f"{base_url_path}/{resume.resume_file}"
            video_path = f"{base_url_path}/{resume.video_url}"

            report_data = {
                "Interview_report": report_url,
                "resume": resume_url,
                "candidate_name": resume.candidate_name,
                "video_url": video_path,
            }
            resume_list.append(report_data)

        return resume_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get resumes: {str(e)}")