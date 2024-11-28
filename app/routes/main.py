from flask import Blueprint, render_template, request, jsonify, current_app
from ..extensions import db
from ..models.candidate import Candidate

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    current_app.logger.info("Accessing index page")
    return render_template('index.html')

@bp.route('/health')
def health():
    current_app.logger.info("Health check requested")
    return jsonify({'status': 'healthy'})

@bp.route('/api/candidates', methods=['GET'])
def get_candidates():
    candidates = Candidate.query.all()
    return jsonify([candidate.to_dict() for candidate in candidates])

@bp.route('/api/candidates', methods=['POST'])
def create_candidate():
    try:
        data = request.get_json()
        candidate = Candidate(
            name=data.get('name'),
            email=data.get('email'),
            phone=data.get('phone'),
            skills=data.get('skills'),
            education=data.get('education'),
            experience=data.get('experience'),
            status='pending'
        )
        db.session.add(candidate)
        db.session.commit()
        return jsonify(candidate.to_dict()), 201
    except Exception as e:
        current_app.logger.error(f"Error creating candidate: {str(e)}")
        return jsonify({'error': 'Failed to create candidate'}), 400

@bp.route('/api/candidates/<int:id>', methods=['GET'])
def get_candidate(id):
    candidate = Candidate.query.get_or_404(id)
    return jsonify(candidate.to_dict())
