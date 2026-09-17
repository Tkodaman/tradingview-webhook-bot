from typing import Dict, Any, List
import time
from core.logger import logger
from schemas.webhook import WebhookSignal, RiskAnalysisResult
from services.data_ingestion.market_feed import market_feed
from services.data_ingestion.news_macro_feed import news_macro_feed
from services.risk_engine.evaluator import risk_evaluator
from services.ai_agent.research_engine import financial_agent

class AutonomousMarketAgent:
    """
    Arka Planda Otomatik Tetiklenen Piyasa Analizör & 10-Skill Denetim Ajanı
    Webhook sinyali geldiğinde:
    1. Canlı teknik piyasa koşullarını ve indikatörleri çeker.
    2. Küresel haber ve makroekonomik duygu analizini (önbellekten) yapar.
    3. Dereceli sayısal risk motorunu çalıştırır.
    4. 10 Borsa Yeteneğini (Skills Suite) eş zamanlı test ve denetimden geçirir.
    5. Sert kural filtresi sonuçlarını ve emir kararını hazırlar.
    """
    def __init__(self):
        self.decision_history: List[Dict[str, Any]] = []
        # Makro analizi önbelleği: sık RSS çekimini önlemek için sınıf düzeyinde sakla
        self._cached_macro: Dict[str, Any] = {}
        self._macro_cache_time: float = 0.0
        self._macro_cache_ttl: float = 600.0  # 10 dakika - makro şok anlık değil
        
        # PRE-COGNITIVE SHADOW AI CACHE
        # Sembol başına taze (son 10 dk) AI kararını tutar
        self.shadow_analysis_cache: Dict[str, Dict[str, Any]] = {}

    def _get_cached_macro(self, symbol: str, macro_tags) -> Dict[str, Any]:
        """
        Makro riski önbellekten al. Eğer önbellek tazeye yeni RSS çekmez,
        zaten kilitli olmayan fallback döner → kritik yolu temiz tutar.
        """
        now = time.time()
        if self._cached_macro and (now - self._macro_cache_time < self._macro_cache_ttl):
            return self._cached_macro  # Önbellekten dön, RSS yok
        try:
            result = news_macro_feed.evaluate_macro_risk(
                symbol=symbol,
                custom_macro_tags=macro_tags
            )
            self._cached_macro = result
            self._macro_cache_time = now
            return result
        except Exception as e:
            logger.warning(f"[MACRO CACHE MISS] RSS erişilemedi, nötr değer kullanılıyor: {e}")
            # Nötr fallback: blok yok, sıfır etki
            return {
                "average_sentiment": 0.0,
                "max_macro_impact": 0.0,
                "macro_risk_score": 30.0,  # nötr - ne çok yüksek ne çok düşük
                "high_risk_alerts": [],
                "recent_news_count": 0,
                "macro_state": "DATA_UNAVAILABLE",
                "data_available": False
            }

    def analyze_and_evaluate(self, signal: WebhookSignal) -> Dict[str, Any]:
        logger.info(f"[AGENT TRIGGERED] Analyzing incoming signal for {signal.symbol} ({signal.action})")

        # Shadow analizleri yalnızca ön-izleme içindir; taze sinyal her zaman yeniden değerlendirilir.
        # Eski bir kararın yeni fiyat/hacim/volatilite koşullarına taşınması güvenli değildir.

        # 1. Teknik & Piyasa Verisi Analizi (hızlı - yerel hesaplama)
        market_analysis = market_feed.analyze_market_conditions(
            symbol=signal.symbol,
            current_price=signal.price,
            indicators=signal.indicators
        )

        # 2. Makroekonomik Analiz (ÖNBELLEKten - RSS yok, blok yok)
        macro_analysis = self._get_cached_macro(signal.symbol, signal.macro_tags)

        # 3. Dereceli Sayısal Risk ve Sert Kurallar Denetimi
        risk_result: RiskAnalysisResult = risk_evaluator.evaluate(
            signal=signal,
            market_analysis=market_analysis,
            macro_analysis=macro_analysis
        )

        # 4. EŞ ZAMANLI 10-SKILL DENETİMİ & TEST MOTORU (Concurrent 10-Skill Inspection)
        skills_audit = financial_agent.audit_tradingview_signal_concurrently(signal)

        decision_payload = {
            "signal": signal.model_dump(),
            "market_analysis": market_analysis,
            "macro_analysis": macro_analysis,
            "risk_assessment": risk_result.model_dump(),
            "skills_audit": skills_audit,
            "agent_verdict": "EXECUTE" if risk_result.passed_hard_rules else "BLOCKED_BY_RISK_ENGINE",
            "_timestamp": time.time()
        }

        # Eğitim ve geçmiş analizi için kararı kaydet
        self.decision_history.append(decision_payload)
        if len(self.decision_history) > 500:
            self.decision_history.pop(0)

        logger.info(
            f"[AGENT VERDICT] {signal.symbol} | Score: {risk_result.raw_risk_score} | "
            f"Level: {risk_result.risk_level} | Skills Score: {skills_audit['overall_skill_score']}/100 ({skills_audit['passed_skills_count']}/10 Passed) | Verdict: {decision_payload['agent_verdict']}"
        )

        return decision_payload

analyzer_agent = AutonomousMarketAgent()

