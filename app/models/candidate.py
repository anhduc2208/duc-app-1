from datetime import datetime
from ..extensions import db

class Candidate(db.Model):
    """Candidate model for storing resume information"""
    __tablename__ = 'candidates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    skills = db.Column(db.Text)  # Store as JSON string
    education = db.Column(db.Text)
    experience = db.Column(db.Text)
    resume_path = db.Column(db.String(255))
    status = db.Column(db.String(20), default='pending')  # pending, reviewed, accepted, rejected
    evaluation = db.Column(db.Text)  # Store AI evaluation
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, name=None, email=None, phone=None, skills=None, 
                 education=None, experience=None, resume_path=None, 
                 status='pending', evaluation=None):
        self.name = name
        self.email = email
        self.phone = phone
        self.skills = skills
        self.education = education
        self.experience = experience
        self.resume_path = resume_path
        self.status = status
        self.evaluation = evaluation

    def __repr__(self):
        return f'<Candidate {self.name or "Unknown"}>'

    def to_dict(self):
        """Convert candidate to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'skills': self.skills,
            'education': self.education,
            'experience': self.experience,
            'resume_path': self.resume_path,
            'status': self.status,
            'evaluation': self.evaluation,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
