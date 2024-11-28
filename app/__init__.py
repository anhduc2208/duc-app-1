from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import logging
from logging.handlers import RotatingFileHandler
from .config import Config
from .extensions import db

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def setup_logging(app):
    """Setup logging configuration"""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'app.log')
    
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=1024 * 1024,
        backupCount=10,
        encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('HR Resume Analyzer startup')

def init_database(app):
    """Initialize database"""
    with app.app_context():
        try:
            # Import all models here
            from .models.candidate import Candidate
            
            # Create tables
            logger.info("Creating database tables...")
            db.create_all()
            
            # Verify tables
            tables = db.engine.table_names()
            logger.info(f"Created tables: {tables}")
            
            if 'candidates' not in tables:
                raise Exception("Failed to create candidates table")
                
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            logger.info("Attempting database recovery...")
            
            try:
                # Drop all tables and recreate
                db.drop_all()
                db.create_all()
                
                # Verify again
                tables = db.engine.table_names()
                logger.info(f"Recreated tables: {tables}")
                
                if 'candidates' not in tables:
                    raise Exception("Failed to create candidates table after recovery")
                    
                logger.info("Database recovery successful")
                
            except Exception as recovery_error:
                logger.error(f"Database recovery failed: {str(recovery_error)}")
                raise

def create_app(config_class=Config):
    """Create and configure the Flask application"""
    try:
        logger.info("Initializing Flask application...")
        app = Flask(__name__)
        app.config.from_object(config_class)
        
        # Setup logging
        setup_logging(app)
        
        # Initialize extensions
        logger.info("Initializing database...")
        db.init_app(app)
        
        # Create upload folder
        logger.info("Creating upload folder...")
        upload_dir = app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        logger.info(f"Upload directory: {upload_dir}")
        
        # Initialize database
        init_database(app)
        
        # Register blueprints
        logger.info("Registering blueprints...")
        from .routes import api_bp, main_bp
        app.register_blueprint(api_bp)
        app.register_blueprint(main_bp)
        
        logger.info("Application initialization completed successfully")
        return app
        
    except Exception as e:
        logger.exception("Error initializing application")
        raise
