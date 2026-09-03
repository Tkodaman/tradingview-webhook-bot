from typing import Dict, Any, List
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
    2. Küresel haber ve makroekonomik duygu analizini yapar.
    3. Dereceli sayısal risk motorunu çalıştırır.
    4. 10 Borsa Yeteneğini (Skills Suite) eş zamanlı test ve denetimden geçirir.
    5. Sert kural filtresi sonuçlarını ve emir kararını hazırlar.
    """
    def __init__(self):
        self.decision_history: List[Dict[str, Any]] = []

    def analyze_and_evaluate(self, signal: WebhookSignal) -> Dict[str, Any]:
        logger.info(f"[AGENT TRIGGERED] Analyzing incoming signal for {signal.symbol} ({signal.action})")

        # 1. Teknik & Piyasa Verisi Analizi
        market_analysis = market_feed.analyze_market_conditions(
            symbol=signal.symbol,
            current_price=signal.price,
            indicators=signal.indicators
        )

        # 2. Makroekonomik, Jeopolitik ve Haber Duygu Analizi
        macro_analysis = news_macro_feed.evaluate_macro_risk(
            symbol=signal.symbol,
            custom_macro_tags=signal.macro_tags
        )

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
            "agent_verdict": "EXECUTE" if risk_result.passed_hard_rules else "BLOCKED_BY_RISK_ENGINE"
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

