import os
from dotenv import load_dotenv
import logging
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

class Config:
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-please-change-in-production')
    DEBUG = os.getenv('FLASK_ENV') == 'development'
    
    # Base Directory Configuration
    BASE_DIR = Path(__file__).resolve().parent.parent
    
    # Upload Configuration
    UPLOAD_FOLDER = os.path.join(BASE_DIR, os.getenv('UPLOAD_FOLDER', 'uploads'))
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB default
    ALLOWED_EXTENSIONS = set(os.getenv('ALLOWED_EXTENSIONS', 'pdf,docx').split(','))
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///' + str(BASE_DIR / 'hr_resume.db'))
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = DEBUG  # Log SQL queries in debug mode
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_ORG_ID = os.getenv('OPENAI_ORG_ID')
    
    # Logging Configuration
    LOG_DIR = os.path.join(BASE_DIR, 'logs')
    LOG_FILE = os.path.join(LOG_DIR, 'app.log')
    LOG_LEVEL = logging.DEBUG if DEBUG else logging.INFO
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 10
    
    @classmethod
    def init_app(cls, app):
        """Initialize application configuration"""
        try:
            # Create necessary directories
            os.makedirs(cls.UPLOAD_FOLDER, exist_ok=True)
            os.makedirs(cls.LOG_DIR, exist_ok=True)
            
            # Validate configuration
            if not cls.SECRET_KEY or cls.SECRET_KEY == 'dev-key-please-change-in-production':
                app.logger.warning("Using default SECRET_KEY. Please set a secure key in production.")
                
            if not cls.OPENAI_API_KEY:
                app.logger.error("OPENAI_API_KEY is not set. AI features will not work.")
                
            if not os.access(cls.UPLOAD_FOLDER, os.W_OK):
                app.logger.error(f"Upload directory {cls.UPLOAD_FOLDER} is not writable")
                
            app.logger.info("Application configuration initialized successfully")
            
        except Exception as e:
            app.logger.error(f"Error initializing application configuration: {str(e)}")
            raise
