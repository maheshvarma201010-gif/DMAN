import logging
import os
import sys
from logging.handlers import RotatingFileHandler

# Define log directory
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

class ColoredFormatter(logging.Formatter):
    """Custom formatter for colored logs in terminal"""
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    blue = "\x1b[34;20m"
    format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format_str + reset,
        logging.INFO: blue + format_str + reset,
        logging.WARNING: yellow + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: bold_red + format_str + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def get_logger(name, log_file=None):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers
    if not logger.handlers:
        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(ColoredFormatter())
        logger.addHandler(ch)

        # Base File handler
        fh = RotatingFileHandler(os.path.join(LOG_DIR, "bot.log"), maxBytes=5*1024*1024, backupCount=2)
        fh.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        logger.addHandler(fh)

        # Specific File handler if provided
        if log_file:
            sfh = RotatingFileHandler(os.path.join(LOG_DIR, log_file), maxBytes=5*1024*1024, backupCount=2)
            sfh.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
            logger.addHandler(sfh)

    return logger

# Pre-defined loggers
bot_logger = get_logger("BOT")
download_logger = get_logger("DOWNLOAD", "download.log")
upload_logger = get_logger("UPLOAD", "upload.log")
error_logger = get_logger("ERROR", "error.log")
ffmpeg_logger = get_logger("FFMPEG", "ffmpeg.log")
db_logger = get_logger("DATABASE")
