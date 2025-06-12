import logging
import sys
from logging import handlers

def setup_logging(log_level=logging.INFO, log_file=None):
    """
    Set up logging for the application.
    """
    logger = logging.getLogger()
    logger.setLevel(log_level)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler
    if log_file:
        fh = handlers.RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

def get_logger(name):
    """
    Get a logger instance with the specified name.
    """
    return logging.getLogger(name) 