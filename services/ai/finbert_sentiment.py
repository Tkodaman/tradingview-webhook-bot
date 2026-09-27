import asyncio
import time
from core.logger import logger

class FastSentimentRadar:
    """
    FinBERT tabanli Sentiment Radari (Otonom ve Cüretkar Mod)
    - Dar bogaz yaratmamak icin Asenkron calisir.
    - Eger 150ms icinde yanit alamazsa engellemez, "Cesur" islem yapar.
    """
    def __init__(self):
        self._model = None
        self._is_loaded = False
        # Asenkron yukleme icin tetik
        asyncio.create_task(self._load_finbert_in_background())

    async def _load_finbert_in_background(self):
        try:
            # Sadece gerektiginde yuklemek icin import transformers here
            logger.info("🧠 [FinBERT] Arka planda AI modeli yukleniyor (Blocklamaz)...")
            from transformers import pipeline
            def load_sync():
                return pipeline("sentiment-analysis", model="ProsusAI/finbert")
            
            self._model = await asyncio.to_thread(load_sync)
            self._is_loaded = True
            logger.info("✅ [FinBERT] AI Sentiment Radari aktif edildi! Cüretkar al-sat icin hazir.")
        except ImportError:
            logger.warning("⚠️ [FinBERT] 'transformers' kutuphanesi yok. Kurulana kadar otonom cesur modda (Always Positive) calisacak. Kurulum: pip install transformers torch")
        except Exception as e:
            logger.error(f"❌ [FinBERT] Model yuklenirken hata: {e}")

    async def analyze_sentiment_fast(self, text: str) -> dict:
        if not self._is_loaded or self._model is None:
            # Model yuklenmediyse botu yavaslatma, hemen YES ver
            return {"label": "positive", "score": 1.0, "note": "MODEL_LOADING_ASSUMED_POSITIVE"}

        def _run_model(t):
            return self._model(t[:2000])[0]

        try:
            # Eger analiz 150 milisaniyeden uzun surerse, timeout atip cesurca onune bakacak.
            result = await asyncio.wait_for(
                asyncio.to_thread(_run_model, text), 
                timeout=0.150  # 150ms dar bogaz onleyici kilidi
            )
            return {
                "label": result["label"],
                "score": float(result["score"]),
                "note": "AI_VERIFIED"
            }
        except asyncio.TimeoutError:
            logger.warning("⏱️ [FinBERT] Analiz 150ms'yi asti! Dar bogaz önlendi, varsayilan olarak işleme geciliyor (Cesur Mod).")
            return {"label": "neutral", "score": 0.5, "note": "TIMEOUT_ASSUMED_NEUTRAL"}
        except Exception as e:
            logger.error(f"FinBERT Hatasi: {e}")
            return {"label": "neutral", "score": 0.5, "note": "ERROR"}

ai_sentiment_radar = FastSentimentRadar()
