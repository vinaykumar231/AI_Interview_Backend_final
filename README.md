# AI Interviewer - Virtual Hiring Assistant

## Overview
The **AI Interviewer** is an innovative virtual assistant designed to automate the candidate interview process. It helps in conducting interviews, recording answers, evaluating responses, and providing valuable insights to recruiters using AI-based analysis. The system supports text-based and voice-based interviews, making the hiring process efficient and objective.

---

## Features

### **Candidate Interview**
- **Automated Interviewing**:
  - Generates dynamic interview questions based on the candidate's resume and job description.
  - Conducts real-time interviews with the candidate using AI-generated questions.
- **Response Evaluation**:
  - Evaluates text-based responses using Natural Language Processing (NLP).
  - Analyzes voice-based responses using speech-to-text conversion and sentiment analysis.
  - Provides scoring for accuracy, relevance, and confidence in answers.
- **Feedback Reports**:
  - Generates and provides detailed feedback reports for candidates, explaining their evaluation scores.

---

### **Recruiter Portal**
- **Dashboard**:
  - View interview results for all candidates.
  - Analyze candidate performance with score breakdowns and insights.
- **Manage Interviews**:
  - Schedule and manage candidate interviews.
  - Review candidate feedback and scores.

---

### **Admin Portal**
- **Dashboard**:
  - View and manage all user accounts (recruiters, candidates).
  - Manage interview schedules and interview data.
- **Data Management**:
  - Manage candidate profiles and job descriptions.
  - Monitor and manage the interview flow and scoring system.

---

## Technology Stack
### **Backend**
- **Framework**: FastAPI
- **Database**: MySQL

### **Frontend**
- **Library**: React.js
- **Styling**: Tailwind CSS

### **AI & NLP**
- **Language Models**: Gemini AI, GPT (for question generation and answer analysis)
- **NLP**: Natural Language Processing (for text-based response analysis)
- **Speech-to-Text**: For analyzing voice responses
- **Sentiment Analysis**: For analyzing tone and confidence in voice-based answers

---

## Installation Instructions

### **Backend**
1. Clone the repository:
   ```bash
   git clone https://github.com/vinaykumar231/AI_Interview_Backend_final.git
   cd AI_Interviewer
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up the database:
   - Create a MySQL database.
   - Update the database connection string in the `settings.py` or `.env` file.
4. Run the application:
   ```bash
   uvicorn main:app --reload
   ```
5. Access the API docs at `http://localhost:8000/docs`.

---

## Database Structure
### **Tables**
- **Users**: Stores recruiter and candidate details.
- **Interviews**: Tracks interview details, including candidate responses and interview scheduling.
- **Questions**: Stores AI-generated interview questions.
- **Responses**: Stores text and voice responses from candidates.
- **Scores**: Stores evaluation scores and analysis results.
- **Feedback**: Stores feedback reports for candidates.

---

## API Endpoints
### **Candidate APIs**
- POST /interview/start: Start an interview for a candidate.
- POST /interview/submit: Submit candidate responses for evaluation.
- GET /interview/results: Retrieve interview results and feedback.
- More Apis

### **Recruiter APIs**
- GET /interviews: Fetch interview results for candidates.
- GET /interview/{id}: View detailed results for a specific interview.s
- More Apis

### **Admin APIs**
- GET /users: Manage recruiter and candidate user details.
- POST /user/create: Create new user accounts (recruiters, candidates).
- GET /interviews: Manage interview schedules.
- More Apis

---

## Future Enhancements
- Integration with video conferencing platforms for live interviews.
- Advanced sentiment analysis for more accurate evaluations.
- Mobile app support for recruiters and candidates.
- Integration with job boards for automatic candidate sourcing.

---

## License
This project is licensed All these things are part of **Maitri AI**..

---

## Author
- Vinay Kumar
- vinaykumar.pydev@gmail.com
