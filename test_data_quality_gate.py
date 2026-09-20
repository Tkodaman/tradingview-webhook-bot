import asyncio
import time

import routers.market_router as market_router


def _snapshot(**overrides):
    now = time.time()
    snapshot = {
        "symbol": "TEST",
        "market": "CRYPTO",
        "price": 100.0,
        "change_pct": 1.0,
        "rsi": 62.0,
        "macd": 0.1,
        "volume_ratio": 1.8,
        "atr_pct": 2.0,
        "adx": 25.0,
        "cmf": 0.2,
        "ema_golden_cross": True,
        "vwap_bullish": True,
        "supertrend_bullish": True,
        "stoch_k": 60.0,
        "missing_fields": [],
        "source_timestamp": now,
        "last_updated_ts": now,
    }
    snapshot.update(overrides)
    return snapshot


def _run_matrix(monkeypatch, snapshot):
    monkeypatch.setattr(
        market_router.tradingview_live_client,
        "fetch_live_market_data",
        lambda: {"TEST": snapshot},
    )
    monkeypatch.setattr(market_router, "_matrix_cache", {"data": None, "ts": 0})
    return asyncio.run(market_router.get_live_buy_sell_wait_matrix())


def test_missing_indicator_blocks_entry(monkeypatch):
    result = _run_matrix(monkeypatch, _snapshot(missing_fields=["rsi"], rsi=None))
    item = result["grouped"]["CRYPTO"][0]

    assert item["decision"] == "WAIT"
    assert item["decision_gate"] == "DATA_BLOCKED"
    assert item["data_quality"] == "INSUFFICIENT"
    assert item["confidence_score"] == 0.0


def test_fresh_complete_snapshot_can_enter_decision_flow(monkeypatch):
    result = _run_matrix(monkeypatch, _snapshot())
    item = result["grouped"]["CRYPTO"][0]

    assert item["decision_gate"] == "ALLOW_ENTRY"
    assert item["data_quality"] == "FULL"
    assert item["data_age_seconds"] < 2.0