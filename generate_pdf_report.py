from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
import json
import matplotlib.pyplot as plt
import os
import numpy as np
import uuid

def generate_pdf(json_file, pdf_file):
    try:
        with open(json_file, 'r') as file:
            analysis_data = json.load(file)
    except Exception as e:
        print(f"Error loading JSON data: {e}")
        return

    
    doc = SimpleDocTemplate(pdf_file, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Interview Analysis Report", styles['Title']))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Transcriptions of Responses:", styles['Heading2']))

    question_fetch = analysis_data.get("questions")
    questions = [
        question_fetch.get('question_1', 'Question not available'),
        question_fetch.get('question_2', 'Question not available'),
        question_fetch.get('question_3', 'Question not available'),
        question_fetch.get('question_4', 'Question not available'),
        question_fetch.get('question_5', 'Question not available')
    ]

    for index, question in enumerate(questions, start=1):  
        question_key = f"question_{index}"  
        story.append(Paragraph(f"Question {index}: {question}", styles['Heading4'])) 
        
        transcription = analysis_data.get('transcriptions', {}).get(question_key, 'Data not available')
        story.append(Paragraph(f"{index}. {transcription}", styles['Normal']))  
        story.append(Spacer(1, 12))  

    story.append(Paragraph("Overall Speech Content Analysis:", styles['Heading2']))
    for key in ['relevance', 'clarity', 'coherence', 'completeness']:
        score_data = analysis_data.get('overall_speech_content_analysis', {}).get(key, {})
        score = score_data.get('score', 'Data not available')
        description = score_data.get('description', 'Description not available')
        story.append(Paragraph(f"{key.capitalize()}: {score}", styles['Normal']))
        story.append(Paragraph(f"Description: {description}", styles['Normal']))
        story.append(Spacer(1, 6))

    story.append(Spacer(1, 12))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Per-Question Feedback:", styles['Heading2']))
    for i in range(1, 6):
        question_key = f"question_{i}"
        feedback_data = analysis_data.get('overall_speech_content_analysis', {}).get('per_question_feedback', {}).get(question_key, {})
        feedback_score = feedback_data.get('score', 'Data not available')
        feedback = feedback_data.get('feedback', 'Feedback not available')
        story.append(Paragraph(f"Question {i} - Score: {feedback_score}", styles['Normal']))
        story.append(Paragraph(f"Feedback: {feedback}", styles['Normal']))
        story.append(Spacer(1, 12))

    story.append(Spacer(1, 12))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Overall Non-Verbal Communication:", styles['Heading2']))
    for key in ['facial_expressions', 'eye_contact', 'body_language']:
        non_verbal_data = analysis_data.get('overall_non_verbal_communication', {}).get(key, {})
        score = non_verbal_data.get('score', 'Data not available')
        description = non_verbal_data.get('description', 'Description not available')
        story.append(Paragraph(f"{key.replace('_', ' ').capitalize()} - Score: {score}", styles['Normal']))
        story.append(Paragraph(f"Description: {description}", styles['Normal']))
        story.append(Spacer(1, 6))

    story.append(Paragraph("Overall Emotional Analysis:", styles['Heading2']))
    emotional_analysis = analysis_data.get('overall_emotional_analysis', {})
    primary_emotions = emotional_analysis.get('primary_emotions', [])
    emotional_consistency = emotional_analysis.get('emotional_consistency', {})
    story.append(Paragraph(f"Primary Emotions: {', '.join(primary_emotions) if primary_emotions else 'Data not available'}", styles['Normal']))
    story.append(Paragraph(f"Emotional Consistency - Score: {emotional_consistency.get('score', 'Data not available')}", styles['Normal']))
    story.append(Paragraph(f"Description: {emotional_consistency.get('description', 'Description not available')}", styles['Normal']))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Overall Audio Analysis:", styles['Heading2']))
    for key in ['audio_quality', 'background_noise_impact', 'tone', 'confidence', 'speech_pace']:
        audio_data = analysis_data.get('overall_audio_analysis', {}).get(key, {})
        score = audio_data.get('score', 'Data not available')
        description = audio_data.get('description', 'Description not available')
        story.append(Paragraph(f"{key.replace('_', ' ').capitalize()} - Score: {score}", styles['Normal']))
        story.append(Paragraph(f"Description: {description}", styles['Normal']))
        story.append(Spacer(1, 6))

    story.append(Paragraph("Overall Performance:", styles['Heading2']))
    overall_performance = analysis_data.get('overall_performance', {})
    story.append(Paragraph(f"Overall Score: {overall_performance.get('overall_score', 'Data not available')}", styles['Normal']))
    story.append(Paragraph(f"Summary of Strengths: {overall_performance.get('summary', {}).get('strengths', 'Data not available')}", styles['Normal']))
    story.append(Paragraph(f"Areas for Improvement: {overall_performance.get('summary', {}).get('areas_for_improvement', 'Data not available')}", styles['Normal']))
    story.append(Spacer(1, 12))

    doc.build(story)

    print(f"PDF saved as {pdf_file}")

json_file = 'analysis_data.json'
pdf_file = 'interview_analysis_report.pdf'

generate_pdf(json_file, pdf_file)
