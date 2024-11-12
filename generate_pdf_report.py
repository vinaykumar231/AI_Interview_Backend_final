from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
import json
import matplotlib.pyplot as plt
import os
import numpy as np
import uuid

# def create_pie_chart(data, title, pie_chart_file):
#     # Ensure no NaN values in data
#     sizes = np.nan_to_num(data.get('sizes', []), nan=0)  # Replace NaN with 0
#     labels = data.get('labels', [])

#     # Check for any NaN values in labels or sizes and handle them
#     if np.any(np.isnan(sizes)):
#         print("Warning: NaN values found in pie chart sizes. Replacing them with 0.")
#         sizes = np.nan_to_num(sizes, nan=0)
    
#     if len(sizes) != len(labels):
#         print("Warning: Sizes and labels length mismatch. Adjusting to ensure alignment.")
#         sizes = sizes[:len(labels)]

#     # Create the pie chart
#     try:
#         plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
#         plt.title(title)
#         plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

#         # Save the pie chart image
#         plt.savefig(pie_chart_file)
#         plt.close()
#     except Exception as e:
#         print(f"Error creating pie chart: {e}")
#         raise

def create_bar_chart(data, title, file_name):
    questions = list(data.keys())
    scores = [data[question]['score'] for question in questions]
    
    plt.figure(figsize=(10, 6))
    plt.bar(questions, scores, color='blue')
    plt.title(title)
    plt.xlabel('Questions')
    plt.ylabel('Scores')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(file_name)
    plt.close()

def create_radar_chart(data, title, file_name):
    categories = list(data.keys())
    values = list(data.values())
    num_vars = len(categories)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()

    values += values[:1]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.fill(angles, values, color='blue', alpha=0.25)
    ax.plot(angles, values, color='blue', linewidth=2)
    ax.set_yticklabels([])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    plt.title(title)
    plt.savefig(file_name)
    plt.close()

def create_line_chart(data, title, file_name):
    scores = list(data.values())
    x_labels = list(data.keys())

    plt.figure(figsize=(10, 6))
    plt.plot(x_labels, scores, marker='o', linestyle='-', color='green')
    plt.title(title)
    plt.xlabel('Assessment Instances')
    plt.ylabel('Overall Score')
    plt.xticks(rotation=45)
    plt.grid()
    plt.tight_layout()
    plt.savefig(file_name)
    plt.close()

def generate_pdf(json_file, pdf_file):
    try:
        # Load JSON data from the provided file
        with open(json_file, 'r') as file:
            analysis_data = json.load(file)
    except Exception as e:
        print(f"Error loading JSON data: {e}")
        return

    # Create pie and bar charts
    # pie_chart_file = f'pie_chart_{uuid.uuid4()}.png'
    bar_chart_file = f'bar_chart_{uuid.uuid4()}.png'
    
    # # Pie chart data
    # pie_data = {
    #     'Relevance': analysis_data['overall_speech_content_analysis']['relevance']['score'],
    #     'Clarity': analysis_data['overall_speech_content_analysis']['clarity']['score'],
    #     'Coherence': analysis_data['overall_speech_content_analysis']['coherence']['score'],
    #     'Completeness': analysis_data['overall_speech_content_analysis']['completeness']['score']
    # }
    # create_pie_chart(pie_data, 'Overall Speech Content Analysis', pie_chart_file)

    # Bar chart data
    bar_data = analysis_data['overall_speech_content_analysis']['per_question_feedback']
    create_bar_chart(bar_data, 'Per-Question Feedback Scores', bar_chart_file)

    # Create a PDF document
    doc = SimpleDocTemplate(pdf_file, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph("Interview Analysis Report", styles['Title']))
    story.append(Spacer(1, 12))

    # Transcriptions & questions
    story.append(Paragraph("Transcriptions of Responses:", styles['Heading2']))

    # Fetching questions directly from analysis_data
    question_fetch = analysis_data.get("questions")
    questions = [
        question_fetch.get('question_1', 'Question not available'),
        question_fetch.get('question_2', 'Question not available'),
        question_fetch.get('question_3', 'Question not available'),
        question_fetch.get('question_4', 'Question not available'),
        question_fetch.get('question_5', 'Question not available')
    ]

    # Loop through questions with enumerate to get index and question
    for index, question in enumerate(questions, start=1):  # start=1 to start numbering from 1
        question_key = f"question_{index}"  # Construct the question key
        story.append(Paragraph(f"Question {index}: {question}", styles['Heading4']))  # Add the question to the story
        
        # Get the transcription for the current question
        transcription = analysis_data.get('transcriptions', {}).get(question_key, 'Data not available')
        story.append(Paragraph(f"{index}. {transcription}", styles['Normal']))  # Add the transcription to the story
        story.append(Spacer(1, 12))  # Add space between entries

    # Overall Speech Content Analysis
    story.append(Paragraph("Overall Speech Content Analysis:", styles['Heading2']))
    for key in ['relevance', 'clarity', 'coherence', 'completeness']:
        score_data = analysis_data.get('overall_speech_content_analysis', {}).get(key, {})
        score = score_data.get('score', 'Data not available')
        description = score_data.get('description', 'Description not available')
        story.append(Paragraph(f"{key.capitalize()}: {score}", styles['Normal']))
        story.append(Paragraph(f"Description: {description}", styles['Normal']))
        story.append(Spacer(1, 6))

    # Add pie chart
    story.append(Spacer(1, 12))
    # story.append(Image(pie_chart_file, width=400, height=300))
    story.append(Spacer(1, 12))

    # Per-Question Feedback
    story.append(Paragraph("Per-Question Feedback:", styles['Heading2']))
    for i in range(1, 6):
        question_key = f"question_{i}"
        feedback_data = analysis_data.get('overall_speech_content_analysis', {}).get('per_question_feedback', {}).get(question_key, {})
        feedback_score = feedback_data.get('score', 'Data not available')
        feedback = feedback_data.get('feedback', 'Feedback not available')
        story.append(Paragraph(f"Question {i} - Score: {feedback_score}", styles['Normal']))
        story.append(Paragraph(f"Feedback: {feedback}", styles['Normal']))
        story.append(Spacer(1, 12))

    # Add bar chart
    story.append(Spacer(1, 12))
    story.append(Image(bar_chart_file, width=400, height=300))
    story.append(Spacer(1, 12))

    # Overall Non-Verbal Communication
    story.append(Paragraph("Overall Non-Verbal Communication:", styles['Heading2']))
    for key in ['facial_expressions', 'eye_contact', 'body_language']:
        non_verbal_data = analysis_data.get('overall_non_verbal_communication', {}).get(key, {})
        score = non_verbal_data.get('score', 'Data not available')
        description = non_verbal_data.get('description', 'Description not available')
        story.append(Paragraph(f"{key.replace('_', ' ').capitalize()} - Score: {score}", styles['Normal']))
        story.append(Paragraph(f"Description: {description}", styles['Normal']))
        story.append(Spacer(1, 6))

    # Overall Emotional Analysis
    story.append(Paragraph("Overall Emotional Analysis:", styles['Heading2']))
    emotional_analysis = analysis_data.get('overall_emotional_analysis', {})
    primary_emotions = emotional_analysis.get('primary_emotions', [])
    emotional_consistency = emotional_analysis.get('emotional_consistency', {})
    story.append(Paragraph(f"Primary Emotions: {', '.join(primary_emotions) if primary_emotions else 'Data not available'}", styles['Normal']))
    story.append(Paragraph(f"Emotional Consistency - Score: {emotional_consistency.get('score', 'Data not available')}", styles['Normal']))
    story.append(Paragraph(f"Description: {emotional_consistency.get('description', 'Description not available')}", styles['Normal']))
    story.append(Spacer(1, 12))

    # Overall Audio Analysis
    story.append(Paragraph("Overall Audio Analysis:", styles['Heading2']))
    for key in ['audio_quality', 'background_noise_impact', 'tone', 'confidence', 'speech_pace']:
        audio_data = analysis_data.get('overall_audio_analysis', {}).get(key, {})
        score = audio_data.get('score', 'Data not available')
        description = audio_data.get('description', 'Description not available')
        story.append(Paragraph(f"{key.replace('_', ' ').capitalize()} - Score: {score}", styles['Normal']))
        story.append(Paragraph(f"Description: {description}", styles['Normal']))
        story.append(Spacer(1, 6))

    # Overall Performance
    story.append(Paragraph("Overall Performance:", styles['Heading2']))
    overall_performance = analysis_data.get('overall_performance', {})
    story.append(Paragraph(f"Overall Score: {overall_performance.get('overall_score', 'Data not available')}", styles['Normal']))
    story.append(Paragraph(f"Summary of Strengths: {overall_performance.get('summary', {}).get('strengths', 'Data not available')}", styles['Normal']))
    story.append(Paragraph(f"Areas for Improvement: {overall_performance.get('summary', {}).get('areas_for_improvement', 'Data not available')}", styles['Normal']))
    story.append(Spacer(1, 12))

    # Build the PDF
    doc.build(story)

    # Clean up generated chart files
    # os.remove(pie_chart_file)
    os.remove(bar_chart_file)

    print(f"PDF saved as {pdf_file}")

# Path to your analysis data and PDF output
json_file = 'analysis_data.json'
pdf_file = 'interview_analysis_report.pdf'

# Generate PDF report
generate_pdf(json_file, pdf_file)
