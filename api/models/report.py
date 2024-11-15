from sqlalchemy import Column, Integer, String, ForeignKey,Text, DateTime, TIMESTAMP,JSON, Boolean
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
import os
import uuid
import shutil
from database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

class Report(Base):
    __tablename__ = "reports1"

    id = Column(Integer, primary_key=True, autoincrement=True)
    hr_id = Column(Integer)
    candidate_name=Column(String(250))
    resume_file=Column(String(255))
    email=Column(String(255))
    report_file_path = Column(String(255))
    video_url=Column(String(255))
    created_on = Column(DateTime, default=func.now())


def save_upload_resume(upload_file: UploadFile) -> str:
    if not upload_file:
        return None

    try:
        unique_filename = str(uuid.uuid4()) + "_" + upload_file.filename
        file_path = os.path.join("static", "uploaded_resume_duringInterview", unique_filename)
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)

        # Return relative URL for use with FastAPI static files
        return f"static/uploaded_resume_duringInterview/{unique_filename}"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
    
def generate_gemini_prompt_for_report_generate(
    question1: str,
    question2: str,
    question3: str,
    question4: str,
    question5: str
) -> str:
    """
    Generate a prompt for evaluating an interview video based on specified questions.

    Args:
        question1 (str): The first interview question.
        question2 (str): The second interview question.
        question3 (str): The third interview question.
        question4 (str): The fourth interview question.
        question5 (str): The fifth interview question.

    Returns:
        str: A formatted prompt for evaluation, structured for JSON output.
    """
    
    prompt = f"""
    Please evaluate the provided interview video where the interviewee is answering the following questions in a single video:

    1. {question1}
    2. {question2}
    3. {question3}
    4. {question4}
    5. {question5}

    Evaluate the response based on the following parameters and provide a detailed evaluation that will be used to generate a PDF report for HR managers. Make sure to format the evaluation clearly and comprehensively:

    1. **Transcription of Responses:**
       -  Provide an accurate transcription for each response to the questions.  in the videos

    2. **Overall Speech Content Analysis:**
       - Relevance: Rate the overall relevance of the answers to the questions on a scale of 1 to 10, and provide a brief explanation for the score given.
       - Clarity: Rate the overall clarity of the speech on a scale of 1 to 10, and provide examples of clear or unclear speech.
       - Coherence: Rate the overall coherence and logical flow of the answers on a scale of 1 to 10, with a brief description of the flow and structure of the responses.
       - Completeness: Rate the overall completeness of the answers on a scale of 1 to 10, and indicate any key points that were well covered or missing.

       **Per-Question Feedback:**
       - For each question, provide a score and a brief narrative on what was well-done and what could be improved. Highlight specific strengths, such as good articulation or strong points made, and areas where the response could be enhanced.

    3. **Overall Non-verbal Communication:**
       - Facial Expressions: Describe and rate the appropriateness of facial expressions on a scale of 1 to 10. Mention if the facial expressions matched the content of the speech or if there were any inconsistencies.
       - Eye Contact: Rate the overall level of eye contact on a scale of 1 to 10, explaining how well the interviewee engaged with the camera (or interviewer).
       - Body Language: Describe and rate the appropriateness of body language on a scale of 1 to 10. Discuss posture, gestures, and any visible signs of nervousness or confidence.

    4. **Overall Emotional Analysis:**
       - Identify the primary emotions displayed throughout the interview (e.g., confidence, nervousness, enthusiasm).
       - Emotional Consistency: Rate the consistency of the emotions with the content of the answers on a scale of 1 to 10. Note any emotional dissonance or alignment.

    5. **Overall Audio Analysis:**
       - Audio Quality: Rate the overall audio quality on a scale of 1 to 10, noting any technical issues that may have affected clarity.
       - Background Noise: Identify any background noise and rate its impact on the answers on a scale of 1 to 10.
       - Tone: Evaluate the tone of the interviewee, discussing whether it was appropriate for the content and context. Rate the tone on a scale of 1 to 10.
       - Confidence: Assess the interviewee’s confidence based on their tone, pace, and speech patterns. Provide a confidence score on a scale of 1 to 10.
       - Speech Pace: Comment on whether the interviewee spoke too quickly, too slowly, or at an appropriate pace. Provide a score for speech pace on a scale of 1 to 10.

    6. **Overall Performance:**
       - Provide an overall performance score on a scale of 1 to 10.
       - Summary:
         - **Strengths**: List key strengths observed throughout the interview, such as clear articulation, strong content, confident delivery, etc.
         - **Areas for Improvement**: Suggest specific areas for improvement, such as speaking more clearly, better structuring of responses, more consistent eye contact, or more appropriate emotional expression.

    **Important Formatting Instructions:**
    - Please ensure that the evaluation is formatted as a single JSON object.
    - The JSON object should include transcriptions for each question and overall scores and descriptions for the other categories.
    - All keys and string values in the JSON must be enclosed in double quotes.
    - The JSON should strictly follow the structure provided below without any extra text or formatting issues.

    **JSON Structure:**
    {{
        "questions": {{
            "question_1": "{question1}",
            "question_2": "{question2}",
            "question_3": "{question3}",
            "question_4": "{question4}",
            "question_5": "{question5}"
        }},

        "transcriptions": {{
            "question_1": "[Transcription for Question 1]",
            "question_2": "[Transcription for Question 2]",
            "question_3": "[Transcription for Question 3]",
            "question_4": "[Transcription for Question 4]",
            "question_5": "[Transcription for Question 5]"
        }},
        "overall_speech_content_analysis": {{
            "relevance": {{
                "score": 0,
                "description": ""
            }},
            "clarity": {{
                "score": 0,
                "description": ""
            }},
            "coherence": {{
                "score": 0,
                "description": ""
            }},
            "completeness": {{
                "score": 0,
                "description": ""
            }},
            "per_question_feedback": {{
                "question_1": {{
                    "score": 0,
                    "feedback": ""
                }},
                "question_2": {{
                    "score": 0,
                    "feedback": ""
                }},
                "question_3": {{
                    "score": 0,
                    "feedback": ""
                }},
                "question_4": {{
                    "score": 0,
                    "feedback": ""
                }},
                "question_5": {{
                    "score": 0,
                    "feedback": ""
                }}
            }}
        }},
        "overall_non_verbal_communication": {{
            "facial_expressions": {{
                "score": 0,
                "description": ""
            }},
            "eye_contact": {{
                "score": 0,
                "description": ""
            }},
            "body_language": {{
                "score": 0,
                "description": ""
            }}
        }},
        "overall_emotional_analysis": {{
            "primary_emotions": [],
            "emotional_consistency": {{
                "score": 0,
                "description": ""
            }}
        }},
        "overall_audio_analysis": {{
            "audio_quality": {{
                "score": 0,
                "description": ""
            }},
            "background_noise_impact": {{
                "score": 0,
                "description": ""
            }},
            "tone": {{
                "score": 0,
                "description": ""
            }},
            "confidence": {{
                "score": 0,
                "description": ""
            }},
            "speech_pace": {{
                "score": 0,
                "description": ""
            }}
        }},
        "overall_performance": {{
            "overall_score": 0,
            "summary": {{
                "strengths": "",
                "areas_for_improvement": ""
            }}
        }}
    }}

    Please analyze the video thoroughly and provide detailed feedback in the exact JSON format specified above.
    Ensure all scores are between 1 and 10, and descriptions are detailed and specific to the candidate's performance.
    The JSON response should be properly formatted and escapable.  Please ensure that the JSON output is complete and valid, with all required fields filled according to the structure provided.
    """
    
    return prompt
