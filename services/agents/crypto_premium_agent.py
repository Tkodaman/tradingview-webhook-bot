import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from typing import Dict, Any, Tuple
import logging
import time

logger = logging.getLogger("CryptoPremiumAgent")
load_dotenv()

class CryptoPremiumAgent:
    def __init__(self):
        self.openai_model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-6-astra")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.api_key = os.getenv("OPENAI_API_KEY_SECONDARY") or os.getenv("OPENAI_API_KEY")
        self.openai_client = None

        if self.api_key:
            self.openai_client = OpenAI(api_key=self.api_key, base_url=self.openai_base_url)
            logger.info(f"[CRYPTO PREMIUM] Model: {self.openai_model_name}")
        else:
            logger.warning("[CRYPTO PREMIUM] OPENAI_API_KEY bulunamadi. Kripto analizi devre disi.")

        self.sentiment_cache = {}
        self.CACHE_TTL = 300  # 5 dakika onbellek

    def evaluate_crypto_sentiment(self, symbol: str, indicators: Dict[str, Any], market_regime: str) -> Tuple[bool, float, str]:
        """
        LLM tabanlı Multi-Agent sosyal duyarlılık analizi.
        Geri dönüş: (is_approved, premium_score (0-10), insight_reasoning)
        Tüm sorgular gpt-6-astra modeline yönlendirilir.
        """
        if not self.openai_client:
            logger.warning("[CRYPTO PREMIUM] OpenAI client yok. Kripto analizi varsayılan (Onay) dönüyor.")
            return True, 7.0, "API Key eksik, varsayılan onay."
            
        # Cache kontrolü
        now = time.time()
        if symbol in self.sentiment_cache:
            cached_data = self.sentiment_cache[symbol]
            if now - cached_data["timestamp"] < self.CACHE_TTL:
                logger.debug(f"[CRYPTO PREMIUM] {symbol} için önbellekten veri dönüldü.")
                return cached_data["is_approved"], cached_data["score"], cached_data["insight"]

        prompt = f"""
Sen State-of-the-Art (SOTA) bir Kripto Sosyal Duyarlılık ve Risk (Premium) ajanısın.
Tek gayen sermayeyi korumaktır. Sadece matematiksel indikatörlere değil, varlığın 
arka planındaki hype (coşku) veya panik (dump) potansiyeline bakarsın.

Varlık: {symbol}
Piyasa Rejimi: {market_regime}
İndikatörler (ATR, Hacim, Trend vs.): {json.dumps(indicators, indent=2)}

Senden beklenen, kriptonun şu anki oynaklık ve duyarlılık profilini analiz etmen:
1. Bu kriptoda anlamsız bir "Pump & Dump" riski var mı?
2. Hacim (volume) yeterli mi? Kriptoda hacim yoksa tuzaktır.
3. Kriptonun arkasındaki olası haber/sosyal beklenti pozitif mi?

Lütfen sadece aşağıdaki formatta, geçerli bir JSON objesi döndür (kod bloğu kullanma, saf JSON dön):
{{
    "is_approved": true veya false,
    "confidence_score": 0.0 ile 10.0 arası ondalıklı bir sayı,
    "insight": "Kararının ardındaki 1-2 cümlelik net açıklama."
}}
"""
        try:
            logger.info(f"[CRYPTO PREMIUM] {symbol} analizi -> model: {self.openai_model_name}")
            response = self.openai_client.chat.completions.create(
                model=self.openai_model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5
            )
            raw_text = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
            result = json.loads(raw_text)
            
            is_app = bool(result.get("is_approved", False))
            score = float(result.get("confidence_score", 0.0))
            insight = str(result.get("insight", "Detay yok."))
            
            logger.info(f"[CRYPTO PREMIUM] {symbol} Analizi -> Onay: {is_app}, Skor: {score}/10 | {insight}")
            
            # Cache'e kaydet
            self.sentiment_cache[symbol] = {
                "timestamp": now,
                "is_approved": is_app,
                "score": score,
                "insight": insight
            }
            
            return is_app, score, insight
            
        except Exception as e:
            logger.error(f"[CRYPTO PREMIUM] LLM Analizi hatası: {e}")
            return False, 0.0, f"Analiz başarısız: {e}"

crypto_premium_agent = CryptoPremiumAgent()
