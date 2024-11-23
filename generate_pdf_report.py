from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
import json

def generate_pdf(json_file, pdf_file):
    try:
        with open(json_file, 'r') as file:
            analysis_data = json.load(file)
    except Exception as e:
        print(f"Error loading JSON data: {e}")
        return

    # Create the document
    doc = SimpleDocTemplate(pdf_file, pagesize=letter)
    styles = getSampleStyleSheet()
    custom_style = ParagraphStyle(
        'Custom',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        leading=12
    )

    story = []

   
    story.append(Paragraph("<b>Interview Analysis Report</b>", styles['Title']))
    story.append(Spacer(1, 12))


    story.append(Paragraph("<b>Transcriptions of Responses:</b>", styles['Heading2']))
    question_fetch = analysis_data.get("questions")
    questions = [
        question_fetch.get('question_1', 'Question not available'),
        question_fetch.get('question_2', 'Question not available'),
        question_fetch.get('question_3', 'Question not available'),
        question_fetch.get('question_4', 'Question not available'),
        question_fetch.get('question_5', 'Question not available')
    ]

    table_data = [["Question", "Transcription"]]
    for index, question in enumerate(questions, start=1):
        question_key = f"question_{index}"
        transcription = analysis_data.get('transcriptions', {}).get(question_key, 'Data not available')
        table_data.append([f"Q{index}: {question}", transcription])


    table = Table(table_data, colWidths=[200, 300])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(table)
    story.append(Spacer(1, 12))

    
    def create_section_table(title, data, keys, key_titles):
        """Helper function to create a section table."""
        story.append(Paragraph(f"<b>{title}</b>", styles['Heading2']))
        table_data = [["Metric", "Score", "Description"]]
        for key in keys:
            score_data = data.get(key, {})
            score = score_data.get('score', 'N/A')
            description = score_data.get('description', 'N/A')
            table_data.append([key_titles.get(key, key.capitalize()), score, description])
        table = Table(table_data, colWidths=[150, 100, 250])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(table)
        story.append(Spacer(1, 12))

   
    create_section_table(
        "Overall Speech Content Analysis",
        analysis_data.get('overall_speech_content_analysis', {}),
        ['relevance', 'clarity', 'coherence', 'completeness'],
        {'relevance': 'Relevance', 'clarity': 'Clarity', 'coherence': 'Coherence', 'completeness': 'Completeness'}
    )

    create_section_table(
        "Overall Non-Verbal Communication",
        analysis_data.get('overall_non_verbal_communication', {}),
        ['facial_expressions', 'eye_contact', 'body_language'],
        {'facial_expressions': 'Facial Expressions', 'eye_contact': 'Eye Contact', 'body_language': 'Body Language'}
    )

    emotional_data = analysis_data.get('overall_emotional_analysis', {})
    primary_emotions = emotional_data.get('primary_emotions', [])
    emotional_consistency = emotional_data.get('emotional_consistency', {})
    story.append(Paragraph("<b>Overall Emotional Analysis</b>", styles['Heading2']))
    story.append(Paragraph(f"Primary Emotions: {', '.join(primary_emotions) if primary_emotions else 'Data not available'}", custom_style))
    story.append(Paragraph(f"Emotional Consistency - Score: {emotional_consistency.get('score', 'N/A')}", custom_style))
    # story.append(Paragraph(f"Description: {emotional_consistency.get('description', 'N/A')}", custom_style))
    story.append(Spacer(1, 12))

    create_section_table(
        "Overall Audio Analysis",
        analysis_data.get('overall_audio_analysis', {}),
        ['audio_quality', 'background_noise_impact', 'tone', 'confidence', 'speech_pace'],
        {'audio_quality': 'Audio Quality', 'background_noise_impact': 'Background Noise Impact', 'tone': 'Tone',
         'confidence': 'Confidence', 'speech_pace': 'Speech Pace'}
    )

    performance_data = analysis_data.get('overall_performance', {})
    story.append(Paragraph("<b>Overall Performance</b>", styles['Heading2']))
    story.append(Paragraph(f"Overall Score: {performance_data.get('overall_score', 'N/A')}", custom_style))
    story.append(Paragraph(f"Strengths: {performance_data.get('summary', {}).get('strengths', 'N/A')}", custom_style))
    story.append(Paragraph(f"Areas for Improvement: {performance_data.get('summary', {}).get('areas_for_improvement', 'N/A')}", custom_style))
    story.append(Spacer(1, 12))

    doc.build(story)
    print(f"PDF saved as {pdf_file}")

json_file = 'analysis_data.json'
pdf_file = 'interview_analysis_report.pdf'
generate_pdf(json_file, pdf_file)

