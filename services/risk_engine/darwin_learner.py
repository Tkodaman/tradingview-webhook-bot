import json
import os
from core.logger import logger

class DarwinLearner:
    """
    [DARWIN EVRİM ÖĞRENME MODÜLÜ]
    Komutan'ın "Sinyali buluyorsun ama SL'de patlıyoruz, öğren artık!" emri üzerine yazılmıştır.
    Görev: Stop patladıktan sonra fiyat uçarsa, o coinin SL makasını bir daha asla patlamaması için genişletmek (+%20).
    """
    def __init__(self):
        self.genetics_file = "data/darwin_genetics.json"
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists("data"):
            os.makedirs("data")
        if not os.path.exists(self.genetics_file):
            with open(self.genetics_file, "w") as f:
                json.dump({}, f)

    def learn_from_failure(self, symbol: str, was_stop_hunted: bool):
        """
        Eğer bir coinde 'Stop-Hunt' (Silkeleme) kurbanı olduysak (SL patladı ama yön doğru çıktıysa),
        Darwin Genetiğini devreye sokup o coinin SL Makas Çarpanını kalıcı olarak genişlet.
        """
        if not was_stop_hunted:
            return

        try:
            with open(self.genetics_file, "r") as f:
                genetics = json.load(f)

            if symbol not in genetics:
                genetics[symbol] = {"wick_multiplier": 1.0, "stop_hunt_count": 0}

            # Her silkeleme kurbanı oluşumuzda kalkanı %20 daha esnet (genişlet)
            current_mult = genetics[symbol]["wick_multiplier"]
            new_mult = min(current_mult + 0.20, 2.5) # En fazla 2.5x katına kadar esnesin
            
            genetics[symbol]["wick_multiplier"] = new_mult
            genetics[symbol]["stop_hunt_count"] += 1

            with open(self.genetics_file, "w") as f:
                json.dump(genetics, f, indent=4)
                
            logger.info(f"🧬 [DARWIN ÖĞRENDİ] {symbol} bizi silkeledi! SL Makası (Kalkan) kalıcı olarak {new_mult}x genişletildi.")
        except Exception as e:
            logger.error(f"Darwin Learning Hatası: {e}")

darwin_learner = DarwinLearner()
