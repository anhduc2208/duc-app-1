import os
import PyPDF2
import docx2txt
import json
import re
from typing import Dict, Any

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ''
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
    except Exception as e:
        print(f"Error extracting text from PDF: {str(e)}")
        return ''

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX file"""
    try:
        text = docx2txt.process(file_path)
        return text
    except Exception as e:
        print(f"Error extracting text from DOCX: {str(e)}")
        return ''

def extract_email(text: str) -> str:
    """Extract email from text"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(email_pattern, text)
    return match.group() if match else ''

def extract_phone(text: str) -> str:
    """Extract phone number from text"""
    phone_pattern = r'(\+\d{1,3}[-.]?)?\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
    match = re.search(phone_pattern, text)
    return match.group() if match else ''

def extract_name(text: str) -> str:
    """Extract name from text (first line or after 'Name:')"""
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if line:
            # Check for "Name:" pattern
            name_match = re.search(r'Name:\s*(.*)', line, re.IGNORECASE)
            if name_match:
                return name_match.group(1)
            # Otherwise return first non-empty line
            return line
    return ''

def extract_skills(text: str) -> list:
    """Extract skills from text"""
    # Common programming languages and technologies
    common_skills = [
        'Python', 'Java', 'JavaScript', 'C++', 'C#', 'Ruby', 'PHP',
        'HTML', 'CSS', 'SQL', 'React', 'Angular', 'Vue', 'Node.js',
        'Django', 'Flask', 'Spring', 'Docker', 'Kubernetes', 'AWS',
        'Azure', 'GCP', 'Git', 'Linux', 'Windows', 'MacOS',
        'Machine Learning', 'AI', 'Data Science', 'DevOps', 'Agile',
        'Scrum', 'Project Management', 'Team Leadership'
    ]
    
    skills = []
    for skill in common_skills:
        if re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE):
            skills.append(skill)
    
    return skills

def extract_education(text: str) -> str:
    """Extract education information"""
    education_section = ''
    education_keywords = ['education', 'academic background', 'qualification', 'degree']
    
    # Try to find education section
    lines = text.split('\n')
    capturing = False
    for line in lines:
        if any(keyword in line.lower() for keyword in education_keywords):
            capturing = True
            education_section = line + '\n'
        elif capturing and line.strip():
            if any(keyword in line.lower() for keyword in ['experience', 'employment', 'work history']):
                break
            education_section += line + '\n'
    
    return education_section.strip()

def extract_experience(text: str) -> str:
    """Extract work experience information"""
    experience_section = ''
    experience_keywords = ['experience', 'employment', 'work history']
    
    # Try to find experience section
    lines = text.split('\n')
    capturing = False
    for line in lines:
        if any(keyword in line.lower() for keyword in experience_keywords):
            capturing = True
            experience_section = line + '\n'
        elif capturing and line.strip():
            if any(keyword in line.lower() for keyword in ['education', 'skills', 'references']):
                break
            experience_section += line + '\n'
    
    return experience_section.strip()

def parse_resume(file_path: str) -> Dict[str, Any]:
    """Parse resume and extract relevant information"""
    # Get file extension
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    # Extract text based on file type
    if ext == '.pdf':
        text = extract_text_from_pdf(file_path)
    elif ext in ['.docx', '.doc']:
        text = extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
    
    if not text:
        raise ValueError("Could not extract text from file")
    
    # Extract information
    parsed_data = {
        'name': extract_name(text),
        'email': extract_email(text),
        'phone': extract_phone(text),
        'skills': json.dumps(extract_skills(text)),  # Convert list to JSON string
        'education': extract_education(text),
        'experience': extract_experience(text)
    }
    
    return parsed_data
