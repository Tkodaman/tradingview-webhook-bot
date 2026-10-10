import os
import requests
import logging
import time

logger = logging.getLogger("telegram_notifier")

_telegram_message_cache = {}

def send_telegram_alert(message: str, parse_mode: str = "HTML"):
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
        "parse_mode": parse_mode
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

def send_telegram_alert_throttled(message: str, throttle_key: str, cooldown_sec: int = 3600, parse_mode: str = "HTML"):
    """
    Belirli bir 'throttle_key' için (örneğin 'HACIM_PATLAMASI_ALGO') verilen süre dolmadan
    Telegram'a aynı tip mesajı tekrar atmaz. Spam engeller.
    """
    now = time.time()
    last = _telegram_message_cache.get(throttle_key, 0.0)
    if (now - last) < cooldown_sec:
        # Süre dolmadı, mesajı atma
        return False
        
    # Süre doldu (veya ilk defa), cache'i güncelle ve gönder
    _telegram_message_cache[throttle_key] = now
    return send_telegram_alert(message, parse_mode=parse_mode)
