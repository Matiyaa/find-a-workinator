import logging
import os
from datetime import datetime

LOG_LEVEL = logging.INFO # Default log level

def setup_logger(name='find_a_workinator', log_level=LOG_LEVEL, log_to_file=True):
    """
    Configure and return a logger with both console and file handlers.
    
    Args:
        name (str): Name of the logger
        log_level (int): Logging level (e.g., logging.DEBUG, logging.INFO)
        log_to_file (bool): Whether to also log to a file
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Clear any existing handlers to avoid duplicates if called multiple times
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler if requested
    if log_to_file:
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        # Create log file with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(logs_dir, f'{name}_{timestamp}.log')
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level) # Log everything to file if set
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.info(f"Logging to file: {log_file}")
    
    return logger

# Optionally, create a default logger instance for easy import
# logger = setup_logger()
