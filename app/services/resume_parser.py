import os
import PyPDF2
import docx2txt
import json
import re
from typing import Dict, Any
import logging
from PIL import Image
import pytesseract
from pdf2image import convert_from_path

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_path: str) -> str:
    """Trích xuất văn bản từ file PDF"""
    text = ""
    try:
        # Thử phương pháp 1: PyPDF2
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        
        # Nếu không trích xuất được text, thử dùng OCR
        if not text.strip():
            logger.info("Không thể trích xuất text trực tiếp, thử dùng OCR")
            images = convert_from_path(file_path)
            for image in images:
                text += pytesseract.image_to_string(image, lang='vie+eng') + "\n"
        
        return text.strip()
    except Exception as e:
        logger.error(f"Lỗi khi đọc file PDF: {str(e)}")
        return ''

def extract_text_from_docx(file_path: str) -> str:
    """Trích xuất văn bản từ file DOCX"""
    try:
        text = docx2txt.process(file_path)
        return text.strip()
    except Exception as e:
        logger.error(f"Lỗi khi đọc file DOCX: {str(e)}")
        return ''

def extract_email(text: str) -> str:
    """Trích xuất email từ văn bản"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    matches = re.findall(email_pattern, text)
    return matches[0] if matches else ''

def extract_phone(text: str) -> str:
    """Trích xuất số điện thoại từ văn bản"""
    # Mẫu cho số điện thoại Việt Nam
    phone_patterns = [
        r'(?:(?:\+|00)84|0)\s*[35789](?:\d\s*){8}',  # +84, 84, 0 + 9 số
        r'(\+\d{1,3}[-.]?)?\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'  # Mẫu chung
    ]
    
    for pattern in phone_patterns:
        matches = re.findall(pattern, text)
        if matches:
            # Chuẩn hóa số điện thoại
            phone = re.sub(r'[-.\s]', '', matches[0])
            return phone
    return ''

def extract_name(text: str) -> str:
    """Trích xuất tên từ văn bản"""
    # Danh sách họ phổ biến tiếng Việt
    vn_surnames = ['Nguyễn', 'Trần', 'Lê', 'Phạm', 'Hoàng', 'Huỳnh', 'Phan', 'Vũ', 'Võ', 'Đặng', 'Bùi', 'Đỗ']
    
    lines = text.split('\n')
    for line in lines[:10]:  # Chỉ kiểm tra 10 dòng đầu
        line = line.strip()
        if not line:
            continue
            
        # Kiểm tra nếu dòng chứa "Họ và tên" hoặc "Name"
        name_match = re.search(r'(?:Họ và tên|Name)[:\s]*(.*)', line, re.IGNORECASE)
        if name_match:
            return name_match.group(1).strip()
            
        # Kiểm tra nếu dòng bắt đầu bằng họ tiếng Việt
        if any(line.startswith(surname) for surname in vn_surnames):
            # Kiểm tra độ dài hợp lý cho tên người
            words = line.split()
            if 2 <= len(words) <= 6:
                return line
    
    # Nếu không tìm thấy theo cách trên, lấy dòng đầu tiên có độ dài hợp lý
    for line in lines[:10]:
        line = line.strip()
        words = line.split()
        if 2 <= len(words) <= 6:
            return line
            
    return ''

def extract_skills(text: str) -> list:
    """Trích xuất kỹ năng từ văn bản"""
    # Danh sách kỹ năng phổ biến
    common_skills = [
        # Kỹ năng lập trình
        'Python', 'Java', 'JavaScript', 'C++', 'C#', 'Ruby', 'PHP',
        'HTML', 'CSS', 'SQL', 'React', 'Angular', 'Vue', 'Node.js',
        'Django', 'Flask', 'Spring', 'Docker', 'Kubernetes', 'AWS',
        'Azure', 'GCP', 'Git', 'Linux', 'Windows', 'MacOS',
        
        # Kỹ năng mềm tiếng Việt
        'Giao tiếp', 'Thuyết trình', 'Làm việc nhóm', 'Quản lý thời gian',
        'Giải quyết vấn đề', 'Tư duy phân tích', 'Sáng tạo',
        
        # Kỹ năng chuyên môn tiếng Việt
        'Quản lý dự án', 'Phân tích dữ liệu', 'Thiết kế', 'Marketing',
        'Kiểm thử', 'Bảo mật', 'Quản trị mạng', 'Trí tuệ nhân tạo',
        'Machine Learning', 'Deep Learning', 'Xử lý ngôn ngữ tự nhiên'
    ]
    
    skills = []
    # Tìm kiếm các kỹ năng trong văn bản
    for skill in common_skills:
        if re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE):
            skills.append(skill)
    
    # Tìm các kỹ năng được liệt kê theo dấu phẩy hoặc bullet points
    skill_sections = re.findall(r'(?:Skills?|Kỹ năng)[:\s]*((?:[^•\n]+(?:,|$))+)', text, re.IGNORECASE)
    if skill_sections:
        for section in skill_sections:
            additional_skills = [s.strip() for s in re.split(r'[,•]', section) if s.strip()]
            skills.extend(additional_skills)
    
    return list(set(skills))  # Loại bỏ trùng lặp

def extract_education(text: str) -> str:
    """Trích xuất thông tin học vấn"""
    education_keywords = [
        'education', 'academic', 'qualification', 'degree', 'university', 'college',
        'học vấn', 'trường', 'đại học', 'cao đẳng', 'bằng cấp', 'chứng chỉ'
    ]
    
    lines = text.split('\n')
    education_section = []
    capturing = False
    
    for line in lines:
        line = line.strip()
        
        # Bắt đầu phần học vấn
        if any(keyword in line.lower() for keyword in education_keywords):
            capturing = True
            education_section.append(line)
            continue
            
        # Kết thúc phần học vấn
        if capturing and (not line or any(keyword in line.lower() for keyword in ['experience', 'work', 'kinh nghiệm', 'công việc'])):
            break
            
        # Thu thập thông tin học vấn
        if capturing and line:
            education_section.append(line)
    
    return '\n'.join(education_section)

def extract_experience(text: str) -> str:
    """Trích xuất kinh nghiệm làm việc"""
    experience_keywords = [
        'experience', 'employment', 'work history', 'professional background',
        'kinh nghiệm', 'công việc', 'dự án', 'làm việc', 'chức vụ'
    ]
    
    lines = text.split('\n')
    experience_section = []
    capturing = False
    
    for line in lines:
        line = line.strip()
        
        # Bắt đầu phần kinh nghiệm
        if any(keyword in line.lower() for keyword in experience_keywords):
            capturing = True
            experience_section.append(line)
            continue
            
        # Kết thúc phần kinh nghiệm
        if capturing and (not line or any(keyword in line.lower() for keyword in ['education', 'học vấn', 'skills', 'kỹ năng'])):
            break
            
        # Thu thập thông tin kinh nghiệm
        if capturing and line:
            experience_section.append(line)
    
    return '\n'.join(experience_section)

def parse_resume(file_path: str) -> Dict[str, Any]:
    """Phân tích hồ sơ và trích xuất thông tin"""
    logger.info(f"Bắt đầu phân tích hồ sơ: {file_path}")
    
    try:
        # Xác định loại file
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        # Trích xuất văn bản dựa trên loại file
        if ext == '.pdf':
            text = extract_text_from_pdf(file_path)
        elif ext in ['.docx', '.doc']:
            text = extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Không hỗ trợ định dạng file: {ext}")
        
        if not text:
            raise ValueError("Không thể trích xuất văn bản từ file")
        
        logger.info("Đã trích xuất văn bản thành công, bắt đầu phân tích")
        
        # Trích xuất thông tin
        name = extract_name(text)
        email = extract_email(text)
        phone = extract_phone(text)
        skills = extract_skills(text)
        education = extract_education(text)
        experience = extract_experience(text)
        
        parsed_data = {
            'name': name,
            'email': email,
            'phone': phone,
            'skills': json.dumps(skills, ensure_ascii=False),  # Hỗ trợ tiếng Việt
            'education': education,
            'experience': experience
        }
        
        logger.info(f"Phân tích hồ sơ thành công: {name}")
        return parsed_data
        
    except Exception as e:
        logger.error(f"Lỗi khi phân tích hồ sơ: {str(e)}")
        raise
