import pytz
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import bcrypt
from pydantic import EmailStr, BaseModel
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from dotenv import load_dotenv
import os


load_dotenv()


######################################################################################################################
                # For sending Email
#######################################################################################################################

async def send_email(subject, email_to, body):
    # Set up the SMTP server
    smtp_server = os.getenv("smtp_server_name")
    smtp_port = os.getenv("smtp_port_name")
    smtp_username = os.getenv("smtp_username_name")  
    smtp_password = os.getenv("smtp_password_name") 
    try:
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  
        server.login(smtp_username, smtp_password)  
        
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = email_to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        server.sendmail(smtp_username, email_to, msg.as_string())
        server.quit()

    except Exception as e:
        
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")