import sys
import os
import argparse

# Add the project root directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import logging configuration
from src.utils.logging_config import setup_logging

# Parse command line arguments
parser = argparse.ArgumentParser(description="Warframe Market API Application")
parser.add_argument('--log-level', 
                    default='INFO',
                    choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                    help='Set the logging level')
parser.add_argument('--no-log-file', 
                    action='store_true',
                    help='Disable logging to file')
args = parser.parse_args()

# Initialize logging
logger = setup_logging(
    log_level=args.log_level,
    log_to_file=not args.no_log_file
)
logger.debug("Application startup initiated")

# Import and run the GUI
from src.gui import main
logger.debug("Initializing GUI")

if __name__ == "__main__":
    try:
        logger.info("Starting Warframe Market API application")
        main()
    except Exception as e:
        logger.exception(f"Unhandled exception: {e}")
        raise
    finally:
        logger.info("Application shutdown complete")