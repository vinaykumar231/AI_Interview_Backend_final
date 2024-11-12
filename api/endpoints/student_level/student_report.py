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
from generate_pdf_report import generate_pdf
from datetime import datetime
import subprocess
import uuid
import shutil
from sqlalchemy.orm import Session
from database import get_db
from ...models.student_level.report import S_Report,save_upload_resume,generate_gemini_prompt_for_report_generate
from ...models.student_level.video import S_Video
from typing import Optional
from ...models.student_level.student_question import S_Question



router = APIRouter()


def save_upload_file(upload_file: UploadFile) :
    if not upload_file:
        return None
    
    try:
        unique_filename = str(uuid.uuid4()) + "_" + upload_file.filename
        file_path = os.path.join("static","student_level", "videos", unique_filename)
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Open the file in binary write mode
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
        
        file_path = file_path.replace("\\", "/")
        return file_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")


@router.post("/upload_videos/student/")
async def upload_video(video: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        saved_file_path = save_upload_file(video)
        video_db = S_Video(
            file_path=saved_file_path,
        )
        db.add(video_db)
        db.commit()
        return {"message": "Video uploaded successfully", "video": video_db.file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
############################################  For Report generate  #######################################################



UPLOAD_DIR = os.path.join(os.getcwd(), 'static',"student_level", 'merge_videos')
if not os.path.exists(UPLOAD_DIR):
    os.mkdir(UPLOAD_DIR)

VIDEOS_DIR1 = os.path.join(os.getcwd(), "static","student_level", "videos")
if not os.path.exists(VIDEOS_DIR1):
    os.mkdir(VIDEOS_DIR1)

UPLOAD_DIR2 = os.path.join(os.getcwd(), 'static',"student_level", 'final_report')
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

@router.post("/analyze/student_report/")
async def analyze_video(email: str = Form(...), resume: UploadFile = File(...), db: Session = Depends(get_db)):
    concatenated_video_file = os.path.join(UPLOAD_DIR, 'concatenated_interview.mp4') 

    try:
        resume_url = save_upload_resume(resume)

        # Gather video files
        video_files = sorted(glob.glob(os.path.join(VIDEOS_DIR1, '*.webm')))
        if len(video_files) < 5:
            raise HTTPException(status_code=400, detail="Not enough video files. Ensure all 5 videos are uploaded.")

        # Concatenate video files
        concatenate_videos(video_files, concatenated_video_file)

        # Upload concatenated video for analysis
        video_file = genai.upload_file(path=concatenated_video_file)

        # Wait until the video processing is done
        while video_file.state.name == "PROCESSING":
            time.sleep(10)
            video_file = genai.get_file(video_file.name)

        if video_file.state.name == "FAILED":
            raise HTTPException(status_code=500, detail="Failed to process video.")

        # Analyze the video using the model
        model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")
        question_db = db.query(S_Question).filter(S_Question.candidate_email == email).all()

        if not question_db:
            raise HTTPException(status_code=404, detail="No questions found for the given email.")

        for question in question_db:
        # Remove trailing commas to avoid tuple assignment
            question1 = question.Qustion1
            question2 = question.Qustion2
            question3 = question.Qustion3
            question4 = question.Qustion4
            question5 = question.Qustion5

        # Generate the dynamic question prompt
        dynamic_question = generate_gemini_prompt_for_report_generate(question1, question2, question3, question4, question5)

        try:
            # Instead of reading from a file, use the dynamically generated question string
            response = model.generate_content([video_file, dynamic_question], request_options={"timeout": 600})
        except FileNotFoundError:
            raise HTTPException(status_code=500, detail="The dynamic question file was not found.")

        # Get the response text and strip any extra whitespace
        analysis_output = response.text.strip()

        #print(f"Analysis Output: {analysis_output}")  # Debugging output

        # Parse the analysis data
        try:
            analysis_data = json.loads(analysis_output)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=500, detail=f"Due to Technical Error file not read please try again: {e}")
       

        # Save analysis data to a JSON file
        json_output_path = 'analysis_output.json'
        with open(json_output_path, 'w') as json_output_file:
            json.dump(analysis_data, json_output_file, indent=4)

        # Clean up video file from the server
        genai.delete_file(video_file.name)

        # Generate PDF from analysis data
        timestamp = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
        pdf_file_path = os.path.join(UPLOAD_DIR2, f"{email}_analysis_report_{timestamp}.pdf")
        generate_pdf(json_output_path, pdf_file_path)

        # Save the report to the database
        utc_now = pytz.utc.localize(datetime.utcnow())
        ist_now = utc_now.astimezone(pytz.timezone('Asia/Kolkata'))

        report_db = S_Report(
            resume_file=resume_url,
            email=email,
            report_file_path=pdf_file_path,
            created_on=ist_now,
        )
        db.add(report_db)
        db.commit()

        return {"result": "Analysis complete", "report_path": pdf_file_path}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(concatenated_video_file):
            try:
                os.remove(concatenated_video_file)
            except Exception as cleanup_error:
                print(f"Error removing concatenated video file: {cleanup_error}")
