from flask import Blueprint, render_template, request, jsonify, current_app, send_from_directory
from werkzeug.utils import secure_filename
import os
from ..extensions import db
from ..models.candidate import Candidate
from ..services.resume_parser import parse_resume
import openai

bp = Blueprint('main', __name__)

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

@bp.route('/api/upload', methods=['POST'])
def upload_resume():
    try:
        if 'resume' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['resume']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            
            # Parse resume
            parsed_data = parse_resume(filepath)
            
            # Create candidate
            candidate = Candidate(
                name=parsed_data.get('name'),
                email=parsed_data.get('email'),
                phone=parsed_data.get('phone'),
                skills=parsed_data.get('skills'),
                education=parsed_data.get('education'),
                experience=parsed_data.get('experience'),
                resume_path=filepath,
                status='pending'
            )
            
            db.session.add(candidate)
            db.session.commit()
            
            return jsonify({
                'message': 'Resume uploaded successfully',
                'candidate': candidate.to_dict()
            }), 201
            
    except Exception as e:
        current_app.logger.error(f"Error uploading resume: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'No message provided'}), 400

        # Get OpenAI API key from environment variable
        openai.api_key = os.environ.get('OPENAI_API_KEY')
        if not openai.api_key:
            return jsonify({'error': 'OpenAI API key not configured'}), 500

        # Get candidate context if provided
        candidate_id = data.get('candidate_id')
        context = ""
        if candidate_id:
            candidate = Candidate.query.get(candidate_id)
            if candidate:
                context = f"""
                Candidate Information:
                Name: {candidate.name}
                Email: {candidate.email}
                Phone: {candidate.phone}
                Skills: {candidate.skills}
                Education: {candidate.education}
                Experience: {candidate.experience}
                Status: {candidate.status}
                """

        # Prepare messages for ChatGPT
        messages = [
            {"role": "system", "content": "You are an HR assistant helping to evaluate resumes and candidates."},
            {"role": "user", "content": f"{context}\n\nUser Question: {data['message']}"}
        ]

        # Call ChatGPT API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )

        return jsonify({
            'message': response.choices[0].message['content'].strip()
        })

    except Exception as e:
        current_app.logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

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
