from pdfminer.high_level import extract_text
import re

class PDFParser:
    def __init__(self, file_path):
        self.file_path = file_path
    
    def extract_text(self):
        """Extract all text from PDF file"""
        return extract_text(self.file_path)
    
    def extract_info(self):
        """Extract basic information from resume"""
        text = self.extract_text()
        
        # Find email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email = re.findall(email_pattern, text)
        
        # Find phone number
        phone_pattern = r'(\+84|0)[0-9]{9,10}'
        phone = re.findall(phone_pattern, text)
        
        # Find name (assume it's in the first line)
        name = text.split('\n')[0].strip()
        
        return {
            'name': name,
            'email': email[0] if email else None,
            'phone': phone[0] if phone else None
        }
    
    def extract_sections(self):
        """Extract different sections from resume"""
        text = self.extract_text()
        sections = {
            'education': '',
            'experience': '',
            'skills': []
        }
        
        lines = text.split('\n')
        current_section = None
        section_text = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect section headers
            line_lower = line.lower()
            if 'education' in line_lower or 'học vấn' in line_lower:
                if current_section:
                    sections[current_section] = '\n'.join(section_text)
                current_section = 'education'
                section_text = []
            elif 'experience' in line_lower or 'kinh nghiệm' in line_lower:
                if current_section:
                    sections[current_section] = '\n'.join(section_text)
                current_section = 'experience'
                section_text = []
            elif 'skills' in line_lower or 'kỹ năng' in line_lower:
                if current_section:
                    sections[current_section] = '\n'.join(section_text)
                current_section = 'skills'
                section_text = []
            elif current_section:
                section_text.append(line)
        
        # Add the last section
        if current_section and section_text:
            if current_section == 'skills':
                sections[current_section] = [skill.strip() for skill in section_text]
            else:
                sections[current_section] = '\n'.join(section_text)
        
        # Extract skills from skills section if it's a string
        if isinstance(sections['skills'], str):
            sections['skills'] = [skill.strip() for skill in sections['skills'].split(',')]
        
        return sections
