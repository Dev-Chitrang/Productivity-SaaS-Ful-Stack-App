import logging
import sys
import os
from logging.handlers import RotatingFileHandler

# Define tracking formats
LOG_FORMAT = "%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"

def setup_logging():
    logger = logging.getLogger("saas_app")
    logger.setLevel(logging.INFO)


    if not logger.handlers:
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "app.log")

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(console_handler)

        file_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=5)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(file_handler)

    return logger

# Single instance importable anywhere across the application
logger = setup_logging()
