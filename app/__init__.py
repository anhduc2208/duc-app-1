from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import logging
from logging.handlers import RotatingFileHandler
from .extensions import db

def create_app():
    app = Flask(__name__)
    
    # Setup logging first
    if not app.debug and not app.testing:
        # Stream logs to stdout for Heroku
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        app.logger.addHandler(stream_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('HR Resume Analyzer startup')
    
    # Load configuration
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Fix for Heroku Postgres URL
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
            app.logger.info("Converted postgres:// to postgresql:// in DATABASE_URL")
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hr_resume.db'
        app.logger.info("Using SQLite database")
    
    app.logger.info(f"Database URI configured: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')
    
    # Initialize extensions
    db.init_app(app)
    app.logger.info("SQLAlchemy initialized")
    
    # Register blueprints
    from .routes import bp
    app.register_blueprint(bp)
    app.logger.info('Registered blueprints')
    
    # Create database tables
    with app.app_context():
        try:
            db.create_all()
            app.logger.info("Database tables created successfully")
        except Exception as e:
            app.logger.error(f"Error creating database tables: {str(e)}")
            # Print full error details
            import traceback
            error_details = traceback.format_exc()
            app.logger.error(f"Full error traceback:\n{error_details}")
            raise
    
    return app
