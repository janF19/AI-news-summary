import os
import logging
from datetime import datetime

def setup_logging():
    """
    Configure logging for the application.
    
    Returns:
        logging.Logger: Configured logger
    """
    # Use /tmp directory for logs in Lambda environment
    log_dir = '/tmp/logs' if os.environ.get('AWS_LAMBDA_FUNCTION_NAME') else 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger("daily_feed")
    logger.setLevel(logging.INFO)
    
    # Check if handlers already exist to avoid duplicates
    if not logger.handlers:
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create file handler
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = f"{log_dir}/daily_feed_{today}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Create formatter and add to handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        # Add handlers to logger
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
    
    return logger