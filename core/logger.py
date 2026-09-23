import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger():
    os.makedirs("logs", exist_ok=True)
    logger = logging.getLogger("bot_logger")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        # Rotating file handler — max 10 MB per file, 5 yedek (toplam ~60 MB)
        file_handler = RotatingFileHandler(
            "logs/trade.log",
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Stream handler
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    return logger

logger = setup_logger()
