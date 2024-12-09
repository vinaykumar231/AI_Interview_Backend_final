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
from typing import Dict, Optional
from ..models.question import Question
import logging
import re
from sqlalchemy.orm import Session, joinedload
from dotenv import load_dotenv
from google.ai.generativelanguage_v1beta.types import content



load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
router = APIRouter()

# save
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

# configure
def configure_gemini_model():
    """Configure Gemini model with response schema"""
    def create_score_description_schema():
        return content.Schema(
            type=content.Type.OBJECT,
            properties={
                "score": content.Schema(type=content.Type.INTEGER),
                "description": content.Schema(type=content.Type.STRING)
            },
            required=["score", "description"]
        )

    def create_response_schema():
        score_schema = create_score_description_schema()
        
        return content.Schema(
            type=content.Type.OBJECT,
            properties={
                "questions": content.Schema(
                    type=content.Type.OBJECT,
                    properties={f"question_{i}": content.Schema(type=content.Type.STRING) for i in range(1, 6)},
                    required=[f"question_{i}" for i in range(1, 6)]
                ),
                "transcriptions": content.Schema(
                    type=content.Type.OBJECT,
                    properties={f"question_{i}": content.Schema(type=content.Type.STRING) for i in range(1, 6)},
                    required=[f"question_{i}" for i in range(1, 6)]
                ),
                "overall_speech_content_analysis": content.Schema(
                    type=content.Type.OBJECT,
                    properties={
                        "relevance": score_schema,
                        "clarity": score_schema,
                        "coherence": score_schema,
                        "completeness": score_schema,
                        "per_question_feedback": content.Schema(
                            type=content.Type.OBJECT,
                            properties={
                                f"question_{i}": content.Schema(
                                    type=content.Type.OBJECT,
                                    properties={
                                        "score": content.Schema(type=content.Type.INTEGER),
                                        "feedback": content.Schema(type=content.Type.STRING)
                                    },
                                    required=["score", "feedback"]
                                ) for i in range(1, 6)
                            },
                            required=[f"question_{i}" for i in range(1, 6)]
                        )
                    },
                    required=["relevance", "clarity", "coherence", "completeness", "per_question_feedback"]
                ),
                "overall_non_verbal_communication": content.Schema(
                    type=content.Type.OBJECT,
                    properties={
                        "facial_expressions": score_schema,
                        "eye_contact": score_schema,
                        "body_language": score_schema
                    },
                    required=["facial_expressions", "eye_contact", "body_language"]
                ),
                "overall_emotional_analysis": content.Schema(
                    type=content.Type.OBJECT,
                    properties={
                        "primary_emotions": content.Schema(
                            type=content.Type.ARRAY,
                            items=content.Schema(type=content.Type.STRING)
                        ),
                        "emotional_consistency": score_schema
                    },
                    required=["primary_emotions", "emotional_consistency"]
                ),
                "overall_audio_analysis": content.Schema(
                    type=content.Type.OBJECT,
                    properties={
                        "audio_quality": score_schema,
                        "background_noise_impact": score_schema,
                        "tone": score_schema,
                        "confidence": score_schema,
                        "speech_pace": score_schema
                    },
                    required=["audio_quality", "background_noise_impact", "tone", "confidence", "speech_pace"]
                ),
                "overall_performance": content.Schema(
                    type=content.Type.OBJECT,
                    properties={
                        "overall_score": content.Schema(type=content.Type.NUMBER),
                        "summary": content.Schema(
                            type=content.Type.OBJECT,
                            properties={
                                "strengths": content.Schema(type=content.Type.STRING),
                                "areas_for_improvement": content.Schema(type=content.Type.STRING)
                            },
                            required=["strengths", "areas_for_improvement"]
                        )
                    },
                    required=["overall_score", "summary"]
                )
            }
        )

    return {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_schema": create_response_schema(),
        "response_mime_type": "application/json"
    }

def generate_gemini_prompt_for_report_generate(questions: Dict[str, str]) -> str:
    """Generate the prompt for Gemini API"""
    return f"""Please evaluate the provided interview video where the interviewee is answering the following questions:

1. {questions['question1']}
2. {questions['question2']}
3. {questions['question3']}
4. {questions['question4']}
5. {questions['question5']}

Provide a detailed evaluation following the structured format for HR managers' PDF report generation, covering:
1. Transcription of responses
- Please provide the transcriptions of the responses from the video.
   - If no transcription is available for a question, assign a score of zero and explicitly mention that no transcription is available.
   - Do not generate AI-based transcriptions if the video lacks one. Explicitly state it.

If no transcriptions are provided, explicitly mention:
"No response provided."
No AI-generated transcription will be attempted.
Scores for all metrics will default to zero.

Evaluation Metrics:

Assign 0 to Relevance, Clarity, Coherence, and Completeness due to the absence of responses.
Non-verbal communication, emotional analysis, and audio analysis scores also default to 0 as they depend on the presence of responses.

2. Speech content analysis (Score out of 10): Assign scores only if relevant answers are present in the audio; otherwise, assign a score of zero.
   - Relevance: 0
   - Clarity: 0
   - Coherence: 0
   - Completeness: 0
   - If no transcription is available for all questions, all scores must default to zero with an explicit mention.

3. Non-verbal communication (Score out of 10): Assign scores only if relevant engagement is observed during responses; otherwise, assign a score of zero.
   - Assess facial expressions, eye contact, body language, and engagement level.
   - Provide scores based on relevance and consistency with the provided responses.

4. Emotional analysis (Score out of 10): Assign scores only if emotional cues align with the responses; otherwise, assign a score of zero.
   - Evaluate emotional authenticity, depth, and consistency.

5. Audio analysis (Score out of 10): Evaluate audio quality and coherence but assign a score of zero if no responses are provided.
   - Assess clarity, tone, pace, and background noise.

6. Overall performance (Score out of 10): Provide a holistic score based on the above criteria, defaulting to zero if no responses are available.

Include a comment explicitly stating the reason for the zero score: "No responses were provided for the questions. Therefore, all evaluation metrics default to zero."
Provide detailed feedback for all Overall performance score assigned (e.g. 0, 5...), including clear reasons to justify the given marks.

If relevant transcription is provide, assign scores from5 to 1 based on the quality of the overall responses.  
   - Score 10: Excellent performance across all criteria with highly relevant, clear, and complete responses.  
   - Score 7-9: Strong performance, with minor gaps or inconsistencies.  
   - Score 5-6: Adequate performance, addressing some questions but with clear gaps in relevance or clarity.
   - Score 2-4: Poor performance with significant gaps or deficiencies in the responses, affecting overall evaluation.

Note: If no transcription is available for all questions:
- Automatically set all scores to 0 (Relevance, Clarity, Coherence, Completeness, etc.).
- Explicitly mention the lack of transcription and that no AI-generated transcription was used.
- Ensure that the evaluation is based solely on the actual responses from the interview.
Provide detailed feedback for all scores assigned (e.g., 0, 5...), including clear reasons to justify the given marks in Strengths Areas for Improvement

The response must be in valid JSON format following the specified schema."""

system_prompt = """You are an advanced AI interviewer and evaluator designed to analyze video interviews. Your primary tasks include:

Transcription: Transcribe interview responses and analyze them based on speech, non-verbal communication, emotions, and audio quality. Ensure strict response segmentation for each question. Clearly separate the transcription for each question without overlap. Assign responses accurately to their respective questions, even if the candidate’s answer spans multiple topics. If no responses are available, clearly state 'No response provided.'
Speech Content Analysis: Assign a score only if the audio contains relevant and coherent responses to the questions; otherwise, assign a score of zero.
Non-verbal Communication Analysis: Evaluate facial expressions, eye contact, and body language during responses. Assign a score of zero if no engagement or responses are present.
Emotional Analysis: Identify primary emotions and assess emotional consistency during responses. If no response is present, assign a score of zero.
Audio Analysis: Assess audio quality, background noise impact, tone, confidence, and speech pace. If no responses are provided, assign a score of zero.
Overall Performance: Summarize the candidate’s strengths, areas for improvement, and provide an overall performance score. If no relevant responses are available, default the score to zero.

Each section of the response must strictly adhere to the schema's properties and required fields. Prioritize clarity, actionable feedback, and detailed observations. Use the uploaded video as the sole source of data for your analysis.
"""


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
        # Verify HR exists
        subquery = (
                    db.query(
                        Resume_Analysis.candidate_email,
                        func.max(Resume_Analysis.uploaded_at).label("latest_resume_hr")  
                    )
                    .filter(Resume_Analysis.candidate_email == email)  
                    .group_by(Resume_Analysis.candidate_email)  
                    .subquery()
                )
        hr_db = (
            db.query(Resume_Analysis)
            .join(
                subquery,
                (Resume_Analysis.candidate_email == subquery.c.candidate_email) &
                (Resume_Analysis.uploaded_at == subquery.c.latest_resume_hr)
            )
            .first() 
        )

        if not hr_db:
            raise HTTPException(status_code=404, detail="HR not found")

        
        logger.info(f"Processing video analysis for email: {email}")

        
        resume_url = save_upload_resume(resume)
        video_url = save_upload_file_video(video)
        logger.info(f"Video saved at: {video_url}")
        
        # Upload to Gemini API
        logger.info("Uploading video to Gemini API")
        video_file = genai.upload_file(video_url)
        
        # Wait for video processing
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
        # question_db = db.query(Question).filter(Question.candidate_email == email).all()
        # if not question_db:
        #     raise HTTPException(status_code=404, detail="No questions found for the given email.")
        
        subquery = (
                db.query(
                    Question.candidate_email,
                    func.max(Question.created_on).label("latest_questions_date")
                )
                .group_by(Question.candidate_email)
                .subquery()
            )

        question_db = (
                db.query(Question)
                .join(
                    subquery,
                    (Question.candidate_email == subquery.c.candidate_email) &
                    (Question.created_on == subquery.c.latest_questions_date)
                )
                .filter(Question.candidate_email == email)  
                .order_by(desc(Question.created_on))  
                .all()
            )
        
        if not question_db:
            raise HTTPException(status_code=404, detail="No questions found for the given email.")
            

        questions = {
            'question1': question_db[0].Qustion1,
            'question2': question_db[0].Qustion2,
            'question3': question_db[0].Qustion3,
            'question4': question_db[0].Qustion4,
            'question5': question_db[0].Qustion5
        }
        print('questions',questions)

        # Configure Gemini model with schema
        generation_config = configure_gemini_model()
        
        # Create model and generate content
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

        # Process the response
        analysis_output = response.text.strip()
        logger.info(f"Raw API response received: {analysis_output[:200]}...")

        # Clean and parse JSON
        try:
            # Remove markdown formatting if present
            cleaned_output = analysis_output
            if "```json" in cleaned_output:
                cleaned_output = cleaned_output.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned_output:
                cleaned_output = cleaned_output.split("```")[1].split("```")[0].strip()
            
            # Clean up JSON formatting
            cleaned_output = cleaned_output.replace("\n", " ").replace("    ", "").strip()
            cleaned_output = re.sub(r',(\s*[}\]])', r'\1', cleaned_output)
            
            # Parse JSON
            analysis_data = json.loads(cleaned_output)
            
        except Exception as e:
            logger.error(f"JSON parsing error: {str(e)}")
            logger.error(f"Raw content causing error: {analysis_output}")
            
            # Fallback to basic structure
            analysis_data = {
                "analysis": {
                    "raw_text": analysis_output,
                    "timestamp": datetime.now().isoformat(),
                    "email": email
                }
            }

        # Save output files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_output_path = os.path.join("static", "final_report", f"{email}_analysis_{timestamp}.json").replace("\\", "/")
        pdf_file_path = os.path.join("static", "final_report", f"{email}_analysis_report_{timestamp}.pdf").replace("\\", "/")

        # Save JSON
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
                "created_on": resume.created_on,
            }
            resume_list.append(report_data)

        return resume_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get resumes: {str(e)}")