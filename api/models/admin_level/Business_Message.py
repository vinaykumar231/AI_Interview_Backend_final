from sqlalchemy import Boolean, Column, Integer, String, ForeignKey,Text, DateTime, TIMESTAMP
from database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class Business_message(Base):
    __tablename__ = 'business_message_tb1' 
    
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255))
    contact_person_name = Column(String(255))
    business_email = Column(String(255))
    phone_number = Column(String(20))
    company_website = Column(String(255))
    company_size = Column(String(50))
    company_description = Column(Text)
    is_checked = Column(Boolean, default=False)  
    status = Column(String(10), default='unchecked')  
    created_on = Column(DateTime, default=func.now(), nullable=False)  