from typing import Dict, Any, Tuple, List
from core.config import settings
from core.logger import logger
from schemas.webhook import WebhookSignal
from services.risk_engine.market_hours import market_hours_validator

class HardRuleEngine:
    """
    Dereceli Sayısal Sert Kural Denetleyicisi & Devre Kesici (Hard-Rule Circuit Breakers)
    Bu katmandaki kurallar gevşetilemez; ihlal halinde emir doğrudan bloke edilir veya yeniden boyutlandırılır.
    """

    @staticmethod
    def evaluate_hard_rules(
        signal: WebhookSignal,
        raw_risk_score: float,
        market_analysis: Dict[str, Any],
        macro_analysis: Dict[str, Any]
    ) -> Tuple[bool, List[str], List[str], float]:
        """
        Dönüş:
        - passed: bool (Emrin işleme alınıp alınamayacağı)
        - rejection_reasons: List[str] (Varsa ret gerekçeleri)
        - triggered_rules: List[str] (Tetiklenen sert kural bildirimleri)
        - adjusted_quantity: float (Risk skoruna göre hesaplanan nihai lot miktarı)
        """
        rejection_reasons = []
        triggered_rules = []
        base_qty = signal.quantity

        # Kural 0: Piyasa Çalışma Saatleri & Seans Denetimi (Market Hours Gatekeeper)
        is_open, mkt_msg, mkt_info = market_hours_validator.is_market_open(signal.symbol)
        if not is_open:
            rejection_reasons.append(mkt_msg)
            triggered_rules.append(f"RULE_MARKET_CLOSED_{mkt_info.get('market', 'UNKNOWN')}")

        # Kural 1: Maksimum Sert Risk Skoru Sınırı (Hard Risk Ceiling)
        if raw_risk_score > settings.max_risk_score_allowed:
            msg = f"SERT STOP: Toplam risk skoru ({raw_risk_score:.1f}) izin verilen tavanı ({settings.max_risk_score_allowed:.1f}) aştı."
            rejection_reasons.append(msg)
            triggered_rules.append("RULE_MAX_RISK_EXCEEDED")

        # Kural 2: Flash Crash / Aşırı Volatilite Devre Kesicisi
        volatility = market_analysis.get("volatility", 0.0)
        if volatility >= settings.flash_crash_volatility_limit:
            msg = f"DEVRE KESİCİ: Volatilite (%{volatility:.2f}) kritik eşiğin (%{settings.flash_crash_volatility_limit:.2f}) üzerinde. Piyasa aşırı çalkantılı."
            rejection_reasons.append(msg)
            triggered_rules.append("RULE_EXTREME_VOLATILITY_LOCK")

        # Kural 2.5: TARİHSEL DENEYİM (EXPERIENCE MEMORY) KURALI
        from services.engine.experience_memory_engine import experience_memory_engine
        memory_result = experience_memory_engine.evaluate_signal_against_memory(
            symbol=signal.symbol,
            action=signal.action,
            indicators=signal.indicators,
            market_regime=market_analysis.get("regime", "BİLİNMİYOR")
        )
        if not memory_result["is_safe"]:
            rejection_reasons.append(memory_result["reason"])
            triggered_rules.append("RULE_EXPERIENCE_MEMORY_BLOCK")
        else:
            # Modify risk score based on memory confidence
            raw_risk_score -= (memory_result["confidence_modifier"] * 10) # Decrease risk if confident
            # KULLANICI ÖDÜL SİSTEMİ (%20 Lot Artışı)
            qty_mult = memory_result.get("qty_multiplier", 1.0)
            if qty_mult > 1.0:
                base_qty = base_qty * qty_mult
                triggered_rules.append(f"RULE_EXPERIENCE_REWARD_LOT_BOOST_X{qty_mult}")

        # Kural 3: Düşük Hacimli Sahte Kırılım (False Breakout) Filtresi — Eşik: Vol.Ratio < 1.2
        volume_ratio = market_analysis.get("volume_ratio", 1.0)
        vol_threshold = getattr(settings, "volume_anomaly_ratio_threshold", 1.2)
        
        # Agresif (Hızlı) Modda Hacim Filtresi Esnetilir
        current_mode = getattr(settings, "current_risk_mode", "NORMAL").upper()
        if current_mode == "AGGRESSIVE":
            vol_threshold = 0.2  # Agresifte çok daha küçük hacim hareketlerine izin ver
            
        if settings.volume_anomalies_filter and volume_ratio < vol_threshold:
            msg = f"HACİM BLOKAJI: Hacim oranı ({volume_ratio:.2f}x) minimum onay eşiğini ({vol_threshold:.1f}x) karşılamıyor — Sahte kırılım (False Breakout) riski."
            rejection_reasons.append(msg)
            triggered_rules.append(f"RULE_LOW_VOLUME_ANOMALY (ratio={volume_ratio:.2f} < threshold={vol_threshold:.1f})")


        # Kural 4: Kritik Makro / Jeopolitik Şok Blokajı
        macro_alerts = macro_analysis.get("high_risk_alerts", [])
        if macro_alerts and macro_analysis.get("macro_risk_score", 0) > 85.0:
            msg = f"MAKRO ŞOK BLOKAJI: Aktif kritik jeopolitik/faiz riski tespit edildi: {macro_alerts[0]}"
            rejection_reasons.append(msg)
            triggered_rules.append("RULE_MACRO_SHOCK_FREEZE")

        # Kural 5: Dinamik Pozisyon Boyutlandırma (Risk-Adjusted Position Sizing)
        adjusted_qty = base_qty
        if not rejection_reasons:
            if raw_risk_score >= settings.high_risk_threshold:
                # Yüksek riskte pozisyonu %60 küçült
                adjusted_qty = round(base_qty * 0.40, 4)
                triggered_rules.append(f"RULE_POSITION_DOWNSCALE_HIGH_RISK (Qty: {base_qty} -> {adjusted_qty})")
            elif raw_risk_score >= settings.moderate_risk_threshold:
                # Orta riskte pozisyonu %25 küçült
                adjusted_qty = round(base_qty * 0.75, 4)
                triggered_rules.append(f"RULE_POSITION_DOWNSCALE_MODERATE_RISK (Qty: {base_qty} -> {adjusted_qty})")
            else:
                # Düşük riskte tam boyut
                triggered_rules.append("RULE_FULL_POSITION_APPROVED")

        passed = len(rejection_reasons) == 0
        if not passed:
            logger.warning(f"[HARD RULES REJECTED] Symbol: {signal.symbol} | Reasons: {rejection_reasons}")
        else:
            logger.info(f"[HARD RULES PASSED] Symbol: {signal.symbol} | Adjusted Qty: {adjusted_qty} | Rules: {triggered_rules}")

        return passed, rejection_reasons, triggered_rules, adjusted_qty
