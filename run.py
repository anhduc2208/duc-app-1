import os
import sys
import logging
from app import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

try:
    app = create_app()
    logger.info("Application created successfully")
except Exception as e:
    logger.error(f"Error creating application: {str(e)}")
    raise

if __name__ == '__main__':
    try:
        port = int(os.environ.get('PORT', 5000))
        logger.info(f"Starting application on port {port}")
        logger.info("Access URLs:")
        logger.info(f"  Local: http://127.0.0.1:{port}")
        logger.info(f"  External: http://0.0.0.0:{port}")
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        logger.error(f"Error starting application: {str(e)}")
        raise
