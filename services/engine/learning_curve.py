"""Recorded-history statistics; never generate preview performance."""
import math
from collections.abc import Mapping


def build_learning_curve(trades):
    valid = []
    for trade in trades:
        row = dict(trade) if isinstance(trade, Mapping) else trade.model_dump()
        if row.get("is_synthetic") or row.get("data_source") == "SYNTHETIC_PREVIEW":
            continue
        pnl = row.get("pnl_amount")
        timestamp = row.get("timestamp")
        if isinstance(pnl, bool) or not isinstance(pnl, (int, float)):
            continue
        if not math.isfinite(pnl) or not isinstance(timestamp, str) or not timestamp:
            continue
        valid.append((timestamp, pnl))
    valid.sort(key=lambda item: item[0])
    wins = 0
    profit = loss = 0.0
    curve = []
    for count, (timestamp, pnl) in enumerate(valid, 1):
        wins += pnl > 0
        profit += max(pnl, 0)
        loss += max(-pnl, 0)
        curve.append({
            "date": timestamp[:10],
            "win_rate": round(wins / count * 100, 1),
            "profit_factor": round(profit / loss, 2) if loss else None,
        })
    if not curve:
        curve = [{
            "date": "KAYIT YOK",
            "win_rate": 0.0,
            "profit_factor": 0.0
        }]
    return {
        "status": "success",
        "data_source": "RECORDED_TRADE_HISTORY" if valid else "UNAVAILABLE",
        "provenance_verified": False,
        "is_synthetic": False,
        "sample_count": len(valid),
        "learning_curve": curve,
    }