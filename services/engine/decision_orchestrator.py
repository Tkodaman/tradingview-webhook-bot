"""Fast, deterministic orchestration gate for order decisions.

This module deliberately avoids LLM/network calls. It annotates every signal and
only blocks explicit hard data failures that cannot be made safe downstream.
"""
import time
from typing import Any, Dict

from core.config import settings


def evaluate_fast_gate(signal: Any) -> Dict[str, Any]:
    indicators = signal.indicators or {}
    missing_fields = []
    warnings = []
    action = str(signal.action).upper()
    symbol = str(signal.symbol).upper()

    if not signal.price or signal.price <= 0:
        return {
            "decision_gate": "BLOCK",
            "hard_block": True,
            "reason": "INVALID_PRICE",
            "missing_fields": ["price"],
            "warnings": [],
        }

    # Veri Tazeliği Kapısı (Data Quality Gate): sinyalin dayandığı piyasa
    # anlık görüntüsü (webhook veya otonom auto-runner) yeterince taze değilse
    # fail-closed davran — eski veriyle işlem tetiklenmez.
    if signal.timestamp_ms:
        age_seconds = max(0.0, (time.time() * 1000 - signal.timestamp_ms) / 1000.0)
        max_age = getattr(settings, "max_internal_signal_age_seconds", 20.0)
        if age_seconds > max_age:
            return {
                "decision_gate": "BLOCK",
                "hard_block": True,
                "reason": "STALE_MARKET_DATA",
                "missing_fields": missing_fields,
                "warnings": [f"data_age_seconds={age_seconds:.1f} > max_age={max_age:.1f}"],
            }

    if "volume_ratio" in indicators and indicators["volume_ratio"] is None:
        missing_fields.append("volume_ratio")
    if "atr_pct" in indicators and indicators["atr_pct"] is None:
        missing_fields.append("atr_pct")

    volatility = indicators.get("volatility", indicators.get("atr_pct"))
    if volatility is not None and float(volatility) >= settings.flash_crash_volatility_limit:
        return {
            "decision_gate": "BLOCK",
            "hard_block": True,
            "reason": "EXTREME_VOLATILITY",
            "missing_fields": missing_fields,
            "warnings": [f"volatility={float(volatility):.2f}"],
        }

    if missing_fields:
        warnings.append("Eksik indikatörler teyit gerektiriyor.")

    if action in ("BUY", "LONG") and symbol.endswith("USDT"):
        volume_ratio = indicators.get("volume_ratio")
        if volume_ratio is not None and float(volume_ratio) < 1.2:
            warnings.append("Kripto hacim teyidi minimum eşiğin altında.")

    return {
        "decision_gate": "WAIT" if missing_fields else "PASS",
        "hard_block": False,
        "reason": "FAST_PREFLIGHT_COMPLETE",
        "missing_fields": missing_fields,
        "warnings": warnings,
    }
