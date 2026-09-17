import os
import json
import google.generativeai as genai
from openai import OpenAI
from typing import Dict, Any, Tuple
import logging
import time

logger = logging.getLogger("CryptoPremiumAgent")

class CryptoPremiumAgent:
    def __init__(self):
        self.llm_provider = os.getenv("LLM_PROVIDER", "gemini").lower()
        self.openai_client = None
        self.gemini_model = None

        if self.llm_provider == "openai":
            openai_model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-6-astra")
            if openai_model_name == "gpt-6-astra":
                self.api_key = os.getenv("OPENAI_API_KEY_SECONDARY") or os.getenv("OPENAI_API_KEY")
            else:
                self.api_key = os.getenv("OPENAI_API_KEY")
            if self.api_key:
                self.openai_client = OpenAI(api_key=self.api_key)
        else:
            self.api_key = os.getenv("GEMINI_API_KEY")
            if self.api_key:
                genai.configure(api_key=self.api_key)
                self.gemini_model = genai.GenerativeModel("gemini-2.0-flash")
            
        self.sentiment_cache = {}
        self.CACHE_TTL = 300  # 5 dakika önbellek

    def evaluate_crypto_sentiment(self, symbol: str, indicators: Dict[str, Any], market_regime: str) -> Tuple[bool, float, str]:
        """
        LLM tabanlı Multi-Agent sosyal duyarlılık analizi.
        Geri dönüş: (is_approved, premium_score (0-10), insight_reasoning)
        """
        if not self.openai_client and not self.gemini_model:
            logger.warning("[CRYPTO PREMIUM] API Key bulunamadı (Gemini/OpenAI). Kripto analizi varsayılan (Onay) dönüyor.")
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
            if self.llm_provider == "openai" and self.openai_client:
                import os
                openai_model_name = os.getenv("OPENAI_MODEL_NAME", "astra-6")
                try:
                    response = self.openai_client.chat.completions.create(
                        model=openai_model_name,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.5
                    )
                    raw_text = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
                except Exception as e:
                    logger.warning(f"[FALLBACK] OpenAI/Codex hatası veya limit aşımı ({e}). Anında Gemini motoruna geçiliyor...")
                    if self.gemini_model:
                        response = self.gemini_model.generate_content(prompt)
                        raw_text = response.text.replace("```json", "").replace("```", "").strip()
                    else:
                        raise Exception("OpenAI API başarısız oldu ve yedek (Gemini) modeli bulunamadı.")
            elif self.gemini_model:
                response = self.gemini_model.generate_content(prompt)
                raw_text = response.text.replace("```json", "").replace("```", "").strip()
            else:
                raise Exception("Provider configured but no client created.")
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
