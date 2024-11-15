# import os
# import google.generativeai as genai
# from google.ai.generativelanguage_v1beta.types import content

# def configure_gemini():
#     """Configure the Gemini API with the provided API key."""
#     genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# def create_response_schema():
#     """Create the schema for the response structure."""
#     return content.Schema(
#         type=content.Type.OBJECT,
#         properties={
#             "questions": content.Schema(
#                 type=content.Type.OBJECT,
#                 properties={
#                     "question_1": content.Schema(type=content.Type.STRING),
#                     "question_2": content.Schema(type=content.Type.STRING),
#                     "question_3": content.Schema(type=content.Type.STRING),
#                     "question_4": content.Schema(type=content.Type.STRING),
#                     "question_5": content.Schema(type=content.Type.STRING),
#                 },
#                 required=["question_1", "question_2", "question_3", "question_4", "question_5"]
#             ),
#             "transcriptions": content.Schema(
#                 type=content.Type.OBJECT,
#                 properties={
#                     "question_1": content.Schema(type=content.Type.STRING),
#                     "question_2": content.Schema(type=content.Type.STRING),
#                     "question_3": content.Schema(type=content.Type.STRING),
#                     "question_4": content.Schema(type=content.Type.STRING),
#                     "question_5": content.Schema(type=content.Type.STRING),
#                 },
#                 required=["question_1", "question_2", "question_3", "question_4", "question_5"]
#             ),
#             "overall_speech_content_analysis": create_speech_analysis_schema(),
#             "overall_non_verbal_communication": create_non_verbal_schema(),
#             "overall_emotional_analysis": create_emotional_analysis_schema(),
#             "overall_audio_analysis": create_audio_analysis_schema(),
#             "overall_performance": create_performance_schema()
#         }
#     )

# def create_score_description_schema():
#     """Create a reusable schema for score and description pairs."""
#     return content.Schema(
#         type=content.Type.OBJECT,
#         properties={
#             "score": content.Schema(type=content.Type.INTEGER),
#             "description": content.Schema(type=content.Type.STRING)
#         },
#         required=["score", "description"]
#     )

# def create_speech_analysis_schema():
#     """Create schema for speech content analysis."""
#     score_schema = create_score_description_schema()
#     feedback_schema = content.Schema(
#         type=content.Type.OBJECT,
#         properties={
#             "score": content.Schema(type=content.Type.INTEGER),
#             "feedback": content.Schema(type=content.Type.STRING)
#         },
#         required=["score", "feedback"]
#     )
    
#     return content.Schema(
#         type=content.Type.OBJECT,
#         properties={
#             "relevance": score_schema,
#             "clarity": score_schema,
#             "coherence": score_schema,
#             "completeness": score_schema,
#             "per_question_feedback": content.Schema(
#                 type=content.Type.OBJECT,
#                 properties={
#                     f"question_{i}": feedback_schema for i in range(1, 6)
#                 },
#                 required=[f"question_{i}" for i in range(1, 6)]
#             )
#         },
#         required=["relevance", "clarity", "coherence", "completeness", "per_question_feedback"]
#     )

# def create_non_verbal_schema():
#     """Create schema for non-verbal communication analysis."""
#     score_schema = create_score_description_schema()
#     return content.Schema(
#         type=content.Type.OBJECT,
#         properties={
#             "facial_expressions": score_schema,
#             "eye_contact": score_schema,
#             "body_language": score_schema
#         },
#         required=["facial_expressions", "eye_contact", "body_language"]
#     )

# def create_emotional_analysis_schema():
#     """Create schema for emotional analysis."""
#     return content.Schema(
#         type=content.Type.OBJECT,
#         properties={
#             "primary_emotions": content.Schema(
#                 type=content.Type.ARRAY,
#                 items=content.Schema(type=content.Type.STRING)
#             ),
#             "emotional_consistency": create_score_description_schema()
#         },
#         required=["primary_emotions", "emotional_consistency"]
#     )

# def create_audio_analysis_schema():
#     """Create schema for audio analysis."""
#     score_schema = create_score_description_schema()
#     return content.Schema(
#         type=content.Type.OBJECT,
#         properties={
#             "audio_quality": score_schema,
#             "background_noise_impact": score_schema,
#             "tone": score_schema,
#             "confidence": score_schema,
#             "speech_pace": score_schema
#         },
#         required=["audio_quality", "background_noise_impact", "tone", "confidence", "speech_pace"]
#     )

# def create_performance_schema():
#     """Create schema for overall performance analysis."""
#     return content.Schema(
#         type=content.Type.OBJECT,
#         properties={
#             "overall_score": content.Schema(type=content.Type.NUMBER),
#             "summary": content.Schema(
#                 type=content.Type.OBJECT,
#                 properties={
#                     "strengths": content.Schema(type=content.Type.STRING),
#                     "areas_for_improvement": content.Schema(type=content.Type.STRING)
#                 },
#                 required=["strengths", "areas_for_improvement"]
#             )
#         },
#         required=["overall_score", "summary"]
#     )

# def create_generation_config():
#     """Create the generation configuration."""
#     return {
#         "temperature": 1,
#         "top_p": 0.95,
#         "top_k": 40,
#         "max_output_tokens": 8192,
#         "response_schema": create_response_schema(),
#         "response_mime_type": "application/json"
#     }

# def create_interview_prompt(questions):
#     """Create the interview evaluation prompt."""
#     return f"""Please evaluate the provided interview video where the interviewee is answering the following questions in a single video:

# 1. {questions['question_1']}
# 2. {questions['question_2']}
# 3. {questions['question_3']}
# 4. {questions['question_4']}
# 5. {questions['question_5']}

# Please provide a detailed evaluation following the structured format for HR managers' PDF report generation.
# The evaluation should cover:
# 1. Transcription of responses
# 2. Speech content analysis
# 3. Non-verbal communication
# 4. Emotional analysis
# 5. Audio analysis
# 6. Overall performance

# The response should be formatted as a JSON object following the specified schema."""

# def evaluate_interview(question1: str, question2: str, question3: str, question4: str, question5: str):
#     """
#     Evaluate an interview video using the Gemini API.
    
#     Args:
#         question1-question5 (str): The interview questions
    
#     Returns:
#         str: JSON formatted evaluation response
#     """
#     # Configure the API
#     configure_gemini()
    
#     # Create the model with generation config
#     model = genai.GenerativeModel(
#         model_name="gemini-1.5-pro-002",
#         generation_config=create_generation_config()
#     )
    
#     # Start chat session
#     chat_session = model.start_chat(history=[])
    
#     # Create and send prompt
#     questions = {
#         "question_1": question1,
#         "question_2": question2,
#         "question_3": question3,
#         "question_4": question4,
#         "question_5": question5
#     }
    
#     prompt = create_interview_prompt(questions)
#     response = chat_session.send_message(prompt)
    
#     return response.text

# if __name__ == "__main__":
#     # Example usage
#     questions = {
#         "what is your name?",
#         "what is your hobby?",
#         "what is your profession?",
#         "project name?",
#         "nickname?"
#     }
#     result = evaluate_interview(*questions)
#     print(result)