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

    # Title
    story.append(Paragraph("<b>Interview Analysis Report</b>", styles['Title']))
    story.append(Spacer(1, 12))

    

    # Add other sections as tables
    def create_section_table(title, data, keys, key_titles):
        """Helper function to create a section table."""
        story.append(Paragraph(f"<b>{title}</b>", styles['Heading2']))
        table_data = [["Metric", "Score", "Description"]]
        for key in keys:
            score_data = data.get(key, {})
            score = score_data.get('score', 'N/A')
            description = score_data.get('description', 'N/A')

            # Wrap text with Paragraph
            metric_paragraph = Paragraph(key_titles.get(key, key.capitalize()), custom_style)
            description_paragraph = Paragraph(description, custom_style)
            table_data.append([metric_paragraph, score, description_paragraph])

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
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),  
        ]))
        story.append(table)
        story.append(Spacer(1, 12))

    # Speech Content Analysis
    create_section_table(
        "Overall Speech Content Analysis",
        analysis_data.get('overall_speech_content_analysis', {}),
        ['relevance', 'clarity', 'coherence', 'completeness'],
        {'relevance': 'Relevance', 'clarity': 'Clarity', 'coherence': 'Coherence', 'completeness': 'Completeness'}
    )

    # Non-Verbal Communication
    create_section_table(
        "Overall Non-Verbal Communication",
        analysis_data.get('overall_non_verbal_communication', {}),
        ['facial_expressions', 'eye_contact', 'body_language'],
        {'facial_expressions': 'Facial Expressions', 'eye_contact': 'Eye Contact', 'body_language': 'Body Language'}
    )

     # Emotional Analysis (Modified to Table Format with Score Column)
    emotional_data = analysis_data.get('overall_emotional_analysis', {})
    primary_emotions = emotional_data.get('primary_emotions', [])
    emotional_consistency = emotional_data.get('emotional_consistency', {})

    # Start with Emotional Analysis title
    story.append(Paragraph("<b>Overall Emotional Analysis</b>", styles['Heading2']))

    # Create a table for emotional analysis
    table_data = [["Primary Emotions", "Score", "Description"]]

    # Add Primary Emotions to table
    primary_emotions_str = ', '.join(primary_emotions) if primary_emotions else 'Data not available'
    emotional_consistency_score = emotional_consistency.get('score', 'N/A')
    emotional_consistency_description = emotional_consistency.get('description', 'N/A')
    
    # Adjust widths for the columns and use Paragraph for text wrapping
    table_data.append([primary_emotions_str, emotional_consistency_score, 
                       Paragraph(emotional_consistency_description, custom_style)])

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
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Ensure top alignment for text wrapping
        ]))
    story.append(table)
    story.append(Spacer(1, 12))

    # Audio Analysis
    create_section_table(
        "Overall Audio Analysis",
        analysis_data.get('overall_audio_analysis', {}),
        ['audio_quality', 'background_noise_impact', 'tone', 'confidence', 'speech_pace'],
        {'audio_quality': 'Audio Quality', 'background_noise_impact': 'Background Noise Impact', 'tone': 'Tone',
         'confidence': 'Confidence', 'speech_pace': 'Speech Pace'}
    )

    # Overall Performance
    performance_data = analysis_data.get('overall_performance', {})
    story.append(Paragraph("<b>Overall Performance</b>", styles['Heading2']))
    story.append(Paragraph(f"Overall Score: {performance_data.get('overall_score', 'N/A')}", custom_style))
    story.append(Paragraph(f"Strengths: {performance_data.get('summary', {}).get('strengths', 'N/A')}", custom_style))
    story.append(Paragraph(f"Areas for Improvement: {performance_data.get('summary', {}).get('areas_for_improvement', 'N/A')}", custom_style))
    story.append(Spacer(1, 12))

    # Section: Transcriptions of Responses
    story.append(Paragraph("<b>Transcriptions of Responses:</b>", styles['Heading2']))
    question_fetch = analysis_data.get("questions", {})
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

        # Use Paragraph to wrap text within table cells
        question_paragraph = Paragraph(f"Q{index}: {question}", custom_style)
        transcription_paragraph = Paragraph(transcription, custom_style)
        table_data.append([question_paragraph, transcription_paragraph])

    # Format table with style
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
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),  
    ]))
    story.append(table)
    story.append(Spacer(1, 12))

    # Build the document
    doc.build(story)
    print(f"PDF saved as {pdf_file}")


# Input JSON and Output PDF
json_file = 'analysis_data.json'
pdf_file = 'interview_analysis_report.pdf'
generate_pdf(json_file, pdf_file)
