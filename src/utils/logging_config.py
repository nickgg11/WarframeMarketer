"""
Logging Configuration Module
---------------------------
Configures logging for the Warframe Market API application.
Provides functions to set up logging with various levels and destinations.
"""

import os
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logging(
    log_level: str = "INFO", 
    log_to_file: bool = True,
    log_dir: str = "logs",
    app_name: str = "warframe_market_api"
) -> logging.Logger:
    """
    Set up logging with the specified configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to a file in addition to console
        log_dir: Directory to store log files
        app_name: Application name used in log file names
        
    Returns:
        Root logger configured with the specified settings
    """
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logs directory if logging to file
    if log_to_file:
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True, parents=True)
        
        # Create log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = log_path / f"{app_name}_{timestamp}.log"
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(numeric_level)
    
    # Remove any existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Console handler (always enabled)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_to_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    
    # Log initialization
    logger.info(f"Logging initialized at level {log_level}")
    if log_to_file:
        logger.info(f"Log file: {log_file}")
    
    if numeric_level == logging.DEBUG:
        logger.debug("Debug logging enabled")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a specific module."""
    return logging.getLogger(name)