from flask import Blueprint, render_template, request, jsonify
from .extensions import db
from .models.candidate import Candidate

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return 'HR Resume Analyzer is running!'

@main.route('/health')
def health():
    return jsonify({'status': 'healthy'})
