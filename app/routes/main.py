from flask import Blueprint, render_template, request, jsonify, current_app
from ..extensions import db
from ..models.candidate import Candidate

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    current_app.logger.info("Accessing index page")
    return 'HR Resume Analyzer is running!'

@bp.route('/health')
def health():
    current_app.logger.info("Health check requested")
    return jsonify({'status': 'healthy'})
