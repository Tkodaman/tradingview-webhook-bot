import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger():
    os.makedirs("logs", exist_ok=True)
    logger = logging.getLogger("bot_logger")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        # Uvicorn multiprocessing on Windows causes WinError 32 with RotatingFileHandler
        file_handler = logging.FileHandler("logs/trade.log", encoding="utf-8")
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Stream handler
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    return logger

logger = setup_logger()
