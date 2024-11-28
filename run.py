import logging
import os
from app import create_app

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logger.info("Starting Flask application...")
    logger.info(f"Access URLs:")
    logger.info(f"  Local: http://127.0.0.1:{port}")
    logger.info(f"  External: http://0.0.0.0:{port}")
    
    app.run(host='0.0.0.0', port=port, debug=False)
