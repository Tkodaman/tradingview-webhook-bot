import os
import requests
import logging

logger = logging.getLogger("telegram_notifier")

def send_telegram_alert(message: str):
    """
    Yüce Divan'dan Telegram'a acil istihbarat / İz Sürücü Stop (Trailing Stop) mesajı gönderir.
    """
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram Bot Token veya Chat ID bulunamadı. Mesaj gönderilemedi.")
        return False
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            return True
        else:
            logger.error(f"Telegram mesajı gönderilemedi: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Telegram API Hatası: {str(e)}")
        return False
