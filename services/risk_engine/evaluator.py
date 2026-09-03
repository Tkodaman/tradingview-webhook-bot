from datetime import datetime, timezone
from typing import Dict, Any
from core.config import settings
from core.logger import logger
from schemas.webhook import WebhookSignal, RiskAnalysisResult
from services.risk_engine.hard_rules import HardRuleEngine

class RiskEvaluator:
    """
    Dereceli Sayısal Risk Analizatörü (0-100 Skorer)
    Teknik risk, makro/jeopolitik risk ve duygu analizini ağırlıklandırarak
    sayısal risk notu üretir ve sert kurallara sevk eder.
    """

    def evaluate(
        self,
        signal: WebhookSignal,
        market_analysis: Dict[str, Any],
        macro_analysis: Dict[str, Any]
    ) -> RiskAnalysisResult:
        tech_risk = market_analysis.get("composite_technical_risk", 50.0)
        macro_risk = macro_analysis.get("macro_risk_score", 50.0)
        
        # Duygu Riski (Pozitif duygu riski düşürür, negatif duygu yükseltir)
        avg_sentiment = macro_analysis.get("average_sentiment", 0.0) # -100 to +100
        sentiment_risk = max(0.0, min(100.0, (50.0 - (avg_sentiment * 0.5))))

        # Ağırlıklı Toplam Risk Skoru (0 - 100)
        raw_risk_score = (
            (tech_risk * settings.weight_technical) +
            (macro_risk * settings.weight_macro) +
            (sentiment_risk * settings.weight_sentiment)
        )
        raw_risk_score = round(max(0.0, min(100.0, raw_risk_score)), 2)

        # Risk Seviyesi Derecelendirme (Graded Risk Tiers)
        if raw_risk_score >= settings.max_risk_score_allowed:
            risk_level = "CRITICAL"
        elif raw_risk_score >= settings.high_risk_threshold:
            risk_level = "HIGH"
        elif raw_risk_score >= settings.moderate_risk_threshold:
            risk_level = "MODERATE"
        else:
            risk_level = "LOW"

        # Güven Skoru (-100 Çok Güvensiz / Karşıt, +100 Yüksek Güven)
        tech_dir = market_analysis.get("technical_direction_score", 0.0)
        action_factor = 1.0 if signal.action == "BUY" else -1.0
        signal_alignment = (tech_dir * action_factor) # + if aligned with trade
        confidence_score = round(max(-100.0, min(100.0, signal_alignment * 0.6 + avg_sentiment * 0.4 - (raw_risk_score * 0.3))), 2)

        # Sert Kurallar Denetimi (Hard-Rule Engine)
        passed, rejections, triggered_rules, adjusted_qty = HardRuleEngine.evaluate_hard_rules(
            signal=signal,
            raw_risk_score=raw_risk_score,
            market_analysis=market_analysis,
            macro_analysis=macro_analysis
        )

        result = RiskAnalysisResult(
            symbol=signal.symbol,
            action=signal.action,
            raw_risk_score=raw_risk_score,
            risk_level=risk_level,
            passed_hard_rules=passed,
            rejection_reasons=rejections,
            adjusted_quantity=adjusted_qty,
            confidence_score=confidence_score,
            technical_score=tech_risk,
            macro_score=macro_risk,
            sentiment_score=round(avg_sentiment, 2),
            hard_rule_triggers=triggered_rules,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

        return result

risk_evaluator = RiskEvaluator()
