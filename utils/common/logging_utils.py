"""
Logging utilities for the class report application.
"""
import logging

def get_logger(name):
    """
    Get a logger with the specified name.
    
    Args:
        name: The name of the logger
        
    Returns:
        A configured logger instance
    """
    # Configure logging if not already configured
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    return logging.getLogger(name) 