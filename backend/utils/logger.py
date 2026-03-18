"""
Logging Configuration
Structured logging for debugging and monitoring
"""

import logging
import sys
from pythonjsonlogger import jsonlogger
from backend.utils.config import settings

def setup_logger(name: str) -> logging.Logger:
    """
    Create a configured logger instance
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    
    if settings.debug_mode:
        # Human-readable format for development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    else:
        # JSON format for production
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s'
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger
