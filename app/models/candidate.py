from datetime import datetime
from ..extensions import db

class Candidate(db.Model):
    """Candidate model for storing resume information"""
    __tablename__ = 'candidates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    resume_path = db.Column(db.String(500))
    resume_text = db.Column(db.Text)
    education = db.Column(db.Text)
    experience = db.Column(db.Text)
    skills = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, processing, processed, error
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Candidate {self.name or "Unknown"}>'

    def to_dict(self):
        """Convert candidate to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'education': self.education,
            'experience': self.experience,
            'skills': self.skills,
            'status': self.status,
            'error_message': self.error_message,
            'resume_text': self.resume_text,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
