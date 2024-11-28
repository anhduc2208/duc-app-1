from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import threading
import time
from datetime import datetime
import logging
import os
from ..models.candidate import Candidate, db
from ..services.gpt_evaluator import GPTEvaluator
from ..services.resume_parser import ResumeParser
from ..config import Config
import openai

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize services
resume_parser = ResumeParser()
gpt_evaluator = GPTEvaluator()

api_bp = Blueprint('api', __name__)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def process_resume_async(file_path: str, candidate_id: int, app):
    """Process resume asynchronously"""
    start_time = time.time()
    logger.info(f"[ASYNC] Starting async processing for candidate {candidate_id}")
    
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"[ASYNC] Resume file not found: {file_path}")
            raise FileNotFoundError(f"Resume file not found: {file_path}")
            
        # Parse resume
        logger.info(f"[ASYNC] About to parse resume file: {file_path}")
        parsed_data = resume_parser.parse(file_path)
        logger.info(f"[ASYNC] Parsed data received: {parsed_data}")
        
        if not parsed_data:
            logger.error("[ASYNC] No data returned from parser")
            raise Exception("Failed to parse resume")
            
        # Update candidate with parsed data
        logger.info(f"[ASYNC] About to update candidate {candidate_id} with parsed data")
        with app.app_context():
            logger.info(f"[ASYNC] Inside app context for candidate {candidate_id}")
            candidate = Candidate.query.get(candidate_id)
            if not candidate:
                logger.error(f"[ASYNC] Candidate {candidate_id} not found")
                return
                
            try:
                logger.info(f"[ASYNC] Updating candidate {candidate_id} data")
                candidate.name = parsed_data.get('name', 'Unknown')
                candidate.email = parsed_data.get('email', '')
                candidate.phone = parsed_data.get('phone', '')
                candidate.education = parsed_data.get('education', '')
                candidate.experience = parsed_data.get('experience', '')
                
                # Convert skills list to comma-separated string
                skills = parsed_data.get('skills', [])
                candidate.skills = ','.join(skills) if skills else ''
                
                candidate.resume_text = parsed_data.get('raw_text', '')
                candidate.status = 'processed'
                candidate.error_message = None
                candidate.updated_at = datetime.utcnow()
                
                logger.info(f"[ASYNC] About to commit changes for candidate {candidate_id}")
                db.session.commit()
                end_time = time.time()
                logger.info(f"[ASYNC] Successfully processed candidate {candidate_id} in {end_time - start_time:.2f} seconds")
                
            except Exception as e:
                logger.error(f"[ASYNC] Error updating candidate data: {str(e)}")
                candidate.status = 'error'
                candidate.error_message = f"Error updating data: {str(e)}"
                candidate.updated_at = datetime.utcnow()
                db.session.commit()
                end_time = time.time()
                logger.error(f"[ASYNC] Failed to process candidate {candidate_id} after {end_time - start_time:.2f} seconds")
            
    except Exception as e:
        logger.exception(f"[ASYNC] Error processing resume for candidate {candidate_id}")
        end_time = time.time()
        logger.error(f"[ASYNC] Processing failed after {end_time - start_time:.2f} seconds")
        
        with app.app_context():
            try:
                logger.info(f"[ASYNC] Updating error status for candidate {candidate_id}")
                candidate = Candidate.query.get(candidate_id)
                if candidate:
                    candidate.status = 'error'
                    candidate.error_message = str(e)
                    candidate.updated_at = datetime.utcnow()
                    db.session.commit()
                    logger.info(f"[ASYNC] Updated candidate {candidate_id} status to error")
            except Exception as e:
                logger.error(f"[ASYNC] Failed to update error status: {str(e)}")
        
@api_bp.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle resume upload"""
    try:
        logger.info("Processing file upload request")
        
        # Check if file was uploaded
        if 'file' not in request.files:
            logger.warning("No file part in request")
            return jsonify({'error': 'Không tìm thấy file trong yêu cầu'}), 400
            
        file = request.files['file']
        if file.filename == '':
            logger.warning("No selected file")
            return jsonify({'error': 'Chưa chọn file'}), 400
            
        if not file or not allowed_file(file.filename):
            logger.warning(f"Invalid file type: {file.filename}")
            return jsonify({'error': 'Loại file không được hỗ trợ. Chỉ chấp nhận PDF và DOCX'}), 400
            
        # Secure the filename and create full path
        filename = secure_filename(file.filename)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        # Save the file
        try:
            file.save(file_path)
            logger.info(f"File saved successfully: {file_path}")
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            return jsonify({'error': 'Lỗi khi lưu file. Vui lòng thử lại.'}), 500
            
        # Create candidate record
        try:
            candidate = Candidate(
                resume_path=file_path,
                status='processing'
            )
            db.session.add(candidate)
            db.session.commit()
            logger.info(f"Created candidate record with ID: {candidate.id}")
        except Exception as e:
            logger.error(f"Error creating candidate record: {str(e)}")
            os.remove(file_path)  # Clean up file if database operation fails
            return jsonify({'error': 'Lỗi khi tạo hồ sơ. Vui lòng thử lại.'}), 500
            
        # Process resume asynchronously
        try:
            thread = threading.Thread(
                target=process_resume_async,
                args=(file_path, candidate.id, current_app._get_current_object())
            )
            thread.start()
            logger.info(f"Started async processing for candidate {candidate.id}")
        except Exception as e:
            logger.error(f"Error starting async processing: {str(e)}")
            candidate.status = 'error'
            candidate.error_message = 'Lỗi khi xử lý CV. Vui lòng thử lại.'
            db.session.commit()
            return jsonify({'error': 'Lỗi khi xử lý CV. Vui lòng thử lại.'}), 500
            
        return jsonify({
            'message': 'File đã được tải lên thành công và đang được xử lý',
            'candidate_id': candidate.id
        }), 200
        
    except Exception as e:
        logger.exception("Unexpected error in upload_file")
        return jsonify({'error': 'Lỗi hệ thống. Vui lòng thử lại sau.'}), 500

@api_bp.route('/api/chat', methods=['POST'])
def chat():
    """Chat about job requirements and resumes"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Vui lòng nhập câu hỏi'}), 400
            
        message = data['message']
        if not isinstance(message, str) or not message.strip():
            return jsonify({'error': 'Câu hỏi không hợp lệ'}), 400
            
        # Get all processed candidates
        candidates = Candidate.query.filter_by(status='processed').all()
        if not candidates:
            return jsonify({'error': 'Chưa có hồ sơ nào được xử lý'}), 404
            
        # Build context from candidates
        context = "Dưới đây là thông tin các ứng viên:\n\n"
        for idx, candidate in enumerate(candidates, 1):
            context += f"Ứng viên {idx}:\n"
            context += f"Họ tên: {candidate.name}\n"
            context += f"Email: {candidate.email}\n"
            context += f"Số điện thoại: {candidate.phone}\n"
            context += f"Học vấn: {candidate.education}\n"
            context += f"Kinh nghiệm: {candidate.experience}\n"
            context += f"Kỹ năng: {candidate.skills}\n"
            if candidate.resume_text:
                context += f"Nội dung CV: {candidate.resume_text[:500]}...\n"
            context += "\n"
            
        # Build prompt
        prompt = f"""Bạn là trợ lý HR giúp phân tích hồ sơ ứng viên. Dựa trên thông tin các ứng viên sau, hãy trả lời câu hỏi này bằng tiếng Việt: {message}

Thông tin ứng viên:
{context}

Vui lòng phân tích kỹ thông tin và đưa ra câu trả lời chi tiết."""
            
        try:
            # Get response from OpenAI
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Bạn là trợ lý HR giúp phân tích hồ sơ ứng viên. Hãy trả lời mọi câu hỏi bằng tiếng Việt một cách chuyên nghiệp và thân thiện."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content
            return jsonify({'response': answer}), 200
            
        except Exception as e:
            logger.error(f"Lỗi khi gọi OpenAI: {str(e)}")
            return jsonify({'error': f'Không thể nhận phản hồi từ AI: {str(e)}'}), 500
            
    except Exception as e:
        logger.error(f"Lỗi trong endpoint chat: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/api/evaluate', methods=['POST'])
def evaluate_resume():
    """Evaluate candidate against job requirements"""
    try:
        data = request.get_json()
        if not data or 'requirements' not in data:
            return jsonify({'error': 'Missing requirements in request'}), 400
            
        requirements = data['requirements']
        if not isinstance(requirements, str) or not requirements.strip():
            return jsonify({'error': 'Invalid requirements format'}), 400
            
        # Get candidate
        candidate_id = data.get('candidate_id')
        if not candidate_id:
            return jsonify({'error': 'Candidate ID is required'}), 400
            
        candidate = Candidate.query.get(candidate_id)
        if not candidate:
            return jsonify({'error': 'Candidate not found'}), 404
            
        if candidate.status != 'processed':
            return jsonify({'error': 'Candidate resume has not been processed yet'}), 400
            
        # Evaluate candidate
        evaluation = gpt_evaluator.evaluate_candidate(
            candidate_data=candidate.to_dict(),
            requirements=requirements
        )
        
        if 'error' in evaluation:
            return jsonify(evaluation), 400
            
        # Update candidate with evaluation
        candidate.evaluation = evaluation
        candidate.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(evaluation), 200
        
    except Exception as e:
        logger.exception("Error evaluating candidate")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/api/analyze-requirements', methods=['POST'])
def analyze_requirements():
    """Analyze job requirements"""
    try:
        data = request.get_json()
        if not data or 'requirements' not in data:
            return jsonify({'error': 'No requirements provided'}), 400
            
        requirements = data['requirements']
        analysis = gpt_evaluator.analyze_job_requirements(requirements)
        
        return jsonify(analysis), 200
        
    except Exception as e:
        logger.exception("Error in analyze_requirements endpoint")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/api/candidates', methods=['GET'])
def get_candidates():
    """Get all candidates"""
    try:
        logger.info("Getting all candidates...")
        candidates = Candidate.query.order_by(Candidate.created_at.desc()).all()
        logger.info(f"Found {len(candidates)} candidates")
        
        # Convert candidates to dictionary format
        candidates_data = []
        for candidate in candidates:
            try:
                candidate_dict = candidate.to_dict()
                candidates_data.append(candidate_dict)
            except Exception as e:
                logger.error(f"Error converting candidate {candidate.id} to dict: {str(e)}")
                continue
                
        logger.info("Successfully retrieved all candidates")
        return jsonify(candidates_data), 200
        
    except Exception as e:
        logger.exception("Error retrieving candidates")
        return jsonify({'error': 'Không thể tải danh sách ứng viên. Vui lòng thử lại sau.'}), 500

@api_bp.route('/candidate/<int:candidate_id>', methods=['GET'])
def get_candidate_by_id(candidate_id):
    """Get candidate by ID"""
    try:
        candidate = Candidate.query.get(candidate_id)
        if not candidate:
            return jsonify({'error': 'Candidate not found'}), 404
            
        return jsonify({
            'id': candidate.id,
            'name': candidate.name,
            'email': candidate.email,
            'phone': candidate.phone,
            'education': candidate.education,
            'experience': candidate.experience,
            'skills': candidate.skills.split(',') if candidate.skills else [],
            'status': candidate.status,
            'error_message': candidate.error_message,
            'created_at': candidate.created_at.isoformat(),
            'updated_at': candidate.updated_at.isoformat()
        }), 200
        
    except Exception as e:
        logger.exception(f"Error getting candidate {candidate_id}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/candidates/<int:id>', methods=['GET'])
def get_candidate(id):
    """Get a specific candidate by ID"""
    try:
        candidate = Candidate.query.get_or_404(id)
        return jsonify(candidate.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/candidates/search', methods=['GET'])
def search_candidates():
    """Search candidates by query and type"""
    try:
        query = request.args.get('q', '').lower()
        search_type = request.args.get('type', 'all')

        if not query:
            return get_candidates()
        
        # Build base query
        base_query = Candidate.query
        
        # Apply search filters based on type
        if search_type == 'name':
            candidates = base_query.filter(Candidate.name.ilike(f'%{query}%')).all()
        elif search_type == 'skills':
            candidates = base_query.filter(Candidate.skills.ilike(f'%{query}%')).all()
        elif search_type == 'education':
            candidates = base_query.filter(Candidate.education.ilike(f'%{query}%')).all()
        elif search_type == 'experience':
            candidates = base_query.filter(Candidate.experience.ilike(f'%{query}%')).all()
        else:  # search all fields
            candidates = base_query.filter(
                db.or_(
                    Candidate.name.ilike(f'%{query}%'),
                    Candidate.email.ilike(f'%{query}%'),
                    Candidate.skills.ilike(f'%{query}%'),
                    Candidate.education.ilike(f'%{query}%'),
                    Candidate.experience.ilike(f'%{query}%')
                )
            ).all()
        
        return jsonify([candidate.to_dict() for candidate in candidates])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/candidates/<int:id>/resume', methods=['GET'])
def download_resume(id):
    """Download a candidate's resume"""
    try:
        candidate = Candidate.query.get_or_404(id)
        return send_from_directory(
            current_app.config['UPLOAD_FOLDER'],
            candidate.resume_file,
            as_attachment=True
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/candidates/<int:id>/evaluate', methods=['POST'])
def evaluate_candidate(id):
    """Evaluate a candidate using GPT"""
    try:
        # Get candidate
        candidate = Candidate.query.get_or_404(id)
        
        # Get requirements from request
        requirements = request.json.get('requirements')
        if not requirements:
            return jsonify({'error': 'Job requirements are required'}), 400
            
        # Initialize GPT evaluator
        from app.services.gpt_evaluator import GPTEvaluator
        evaluator = GPTEvaluator()
        
        # Get evaluation
        evaluation = evaluator.evaluate_candidate(
            candidate_data=candidate.to_dict(),
            requirements=requirements
        )
        
        if 'error' in evaluation:
            return jsonify({'error': evaluation['error']}), 500
            
        return jsonify(evaluation), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/chat', methods=['POST'])
def chat_with_gpt():
    """Chat with GPT about job requirements"""
    try:
        # Log request
        logger.debug(f"Received chat request: {request.json}")
        
        # Get message from request
        message = request.json.get('message')
        if not message:
            logger.error("No message provided in request")
            return jsonify({'error': 'Message is required'}), 400
            
        # Initialize GPT evaluator
        from app.services.gpt_evaluator import GPTEvaluator
        evaluator = GPTEvaluator()
        
        # Call GPT API
        logger.debug("Calling GPT API...")
        response = evaluator.chat_about_job(message)
        logger.debug(f"GPT API response: {response}")
        
        if 'error' in response:
            logger.error(f"Error from GPT API: {response['error']}")
            return jsonify({'error': response['error']}), 500
            
        return jsonify(response), 200
        
    except Exception as e:
        logger.exception("Error in chat endpoint")
        return jsonify({'error': str(e)}), 500
