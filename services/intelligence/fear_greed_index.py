"""
Crypto Fear & Greed Index Entegrasyonu
Kaynak: https://alternative.me/crypto/fear-and-greed-index/
Cache: 10 dakika (API'ye asiri yuk bindirme)
"""
import time
import requests
from typing import Optional
from dataclasses import dataclass
from core.logger import logger


@dataclass
class FearGreedAssessment:
    score: int
    classification: str
    should_block: bool
    bonus_score: float
    block_reason: str
    data_age_minutes: float


class FearGreedIndexClient:
    API_URL = "https://api.alternative.me/fng/"
    CACHE_TTL_SECONDS = 600  # 10 dakika

    def __init__(self):
        self._cached_score: Optional[int] = None
        self._cached_classification: Optional[str] = None
        self._cache_timestamp: float = 0.0

    def _fetch_from_api(self) -> bool:
        try:
            resp = requests.get(self.API_URL, timeout=8)
            resp.raise_for_status()
            data = resp.json()["data"][0]
            self._cached_score = int(data["value"])
            self._cached_classification = data["value_classification"]
            self._cache_timestamp = time.time()
            logger.info(f"[FEAR&GREED] Guncellendi: {self._cached_score}/100 --- {self._cached_classification}")
            return True
        except Exception as e:
            logger.warning(f"[FEAR&GREED] API hatasi: {e}. Onbellek kullaniliyor.")
            return False

    def _is_cache_valid(self) -> bool:
        return (self._cached_score is not None and (time.time() - self._cache_timestamp) < self.CACHE_TTL_SECONDS)

    def get_assessment(self) -> FearGreedAssessment:
        if not self._is_cache_valid():
            self._fetch_from_api()

        if self._cached_score is None:
            return FearGreedAssessment(score=50, classification="Neutral (API Unavailable)", should_block=False, bonus_score=0.0, block_reason="", data_age_minutes=0.0)

        score = self._cached_score
        classification = self._cached_classification or "Unknown"
        age_minutes = (time.time() - self._cache_timestamp) / 60.0

        if score >= 80:
            return FearGreedAssessment(score=score, classification=classification, should_block=True, bonus_score=0.0, block_reason=f"FOMO BLOKAJI: Fear & Greed Endeksi {score}/100 ({classification}). Piyasa asiri iyimser --- tepe yakin. Yeni alim yapilmiyor.", data_age_minutes=age_minutes)
        if score >= 65:
            return FearGreedAssessment(score=score, classification=classification, should_block=False, bonus_score=0.0, block_reason=f"UYARI: Acgozluluk bolgesi ({score}/100). Dusuk lot onerilir.", data_age_minutes=age_minutes)
        if 40 <= score < 65:
            return FearGreedAssessment(score=score, classification=classification, should_block=False, bonus_score=0.0, block_reason="", data_age_minutes=age_minutes)
        if 20 <= score < 40:
            return FearGreedAssessment(score=score, classification=classification, should_block=False, bonus_score=1.5, block_reason="", data_age_minutes=age_minutes)

        # score < 20 - Asiri Korku
        return FearGreedAssessment(score=score, classification=classification, should_block=False, bonus_score=3.5, block_reason="", data_age_minutes=age_minutes)


fear_greed_client = FearGreedIndexClient()
