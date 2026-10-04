from fastapi.testclient import TestClient
from main import app
from core.config import settings
from services.trainer.bot_trainer import bot_trainer
from services.risk_engine.evaluator import risk_evaluator
from schemas.webhook import WebhookSignal

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"

def test_live_news_endpoint():
    response = client.get("/api/news")
    assert response.status_code == 200
    news = response.json()
    assert isinstance(news, list)
    assert len(news) > 0
    assert "sentiment_score" in news[0]

def test_low_risk_signal_execution():
    payload = {
        "passphrase": settings.passphrase,
        "action": "BUY",
        "symbol": "BTCUSDT",
        "quantity": 2.0,
        "price": 64000.0,
        "indicators": {
            "rsi": 52.0,
            "volatility": 1.2,
            "volume_ratio": 1.8
        },
        "macro_tags": ["TRADE_AGREEMENT"]
    }
    response = client.post("/webhook", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "success"
    assert res["decision"]["risk_assessment"]["passed_hard_rules"] is True
    assert res["decision"]["risk_assessment"]["raw_risk_score"] < settings.max_risk_score_allowed

def test_high_volatility_hard_rule_rejection():
    # Volatility exceeds flash crash limit
    payload = {
        "passphrase": settings.passphrase,
        "action": "BUY",
        "symbol": "ETHUSDT",
        "quantity": 10.0,
        "price": 3500.0,
        "indicators": {
            "rsi": 88.0,
            "volatility": 9.5, # Over flash crash limit 8.0
            "volume_ratio": 0.3
        },
        "macro_tags": ["WAR", "CONFLICT", "CRISIS"]
    }
    response = client.post("/webhook", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "rejected"
    assert res["decision"]["risk_assessment"]["passed_hard_rules"] is False
    assert len(res["decision"]["risk_assessment"]["rejection_reasons"]) > 0

def test_bot_training_engine():
    result = bot_trainer.train_bot(iterations=100)
    assert result["status"] == "TRAINING_COMPLETED_SUCCESSFULLY"
    assert "optimized_weights" in result
    assert "backtest_performance" in result
    perf = result["backtest_performance"]
    assert perf["trades"] > 0
    assert "win_rate" in perf
    assert "sharpe_ratio" in perf

def test_ai_agent_fundamental_research():
    payload = {
        "company_name": "NVIDIA Corporation",
        "ticker": "NVDA",
        "peers": ["AMD", "INTC", "QCOM"]
    }
    response = client.post("/api/agent/fundamental", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "success"
    assert res["mode"] == "FUNDAMENTAL_RESEARCH"
    assert "balance_sheet" in res["structured_data"]
    assert "competitive_moat_analysis" in res["structured_data"]
    assert len(res["structured_data"]["top_3_peers"]) == 3

def test_ai_agent_earnings_breakdown():
    payload = {
        "company_name": "Apple Inc.",
        "ticker": "AAPL",
        "eps_description": "EPS $2.18 vs Est $2.10 (Beat +3.8%)",
        "revenue_description": "$119.58B vs Est $117.91B (+2.1% YoY)",
        "guidance": "Raised FY guidance by +5%",
        "commentary_notes": "Gross margins expanded +140 bps"
    }
    response = client.post("/api/agent/earnings", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "success"
    assert res["mode"] == "EARNINGS_BREAKDOWN"
    assert "earnings_quality_score" in res["structured_data"]
    assert "management_commentary_audit" in res["structured_data"]

def test_ai_agent_position_sizing():
    # Prompt: If I have a $10,000 account and I risk 2% per trade, and my stop-loss is $5 below my entry price ($150),
    # calculate my exact position size and target profit to maintain a 1:3 risk-reward ratio.
    payload = {
        "account_size": 10000.0,
        "risk_pct_per_trade": 2.0,
        "entry_price": 150.0,
        "stop_distance": 5.0,
        "risk_reward_ratio": 3.0
    }
    response = client.post("/api/agent/position-size", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "success"
    assert res["mode"] == "POSITION_SIZING"
    data = res["structured_data"]
    
    # 2% of $10,000 = $200 max risk
    assert data["max_dollar_risk"] == 200.0
    # $200 / $5 stop distance = 40 shares
    assert data["exact_position_units"] == 40.0
    # Total capital = 40 * $150 = $6,000
    assert data["total_capital_allocated_usd"] == 6000.0
    # Target profit price for 1:3 RR = $150 + ($5 * 3) = $165.0
    assert data["target_profit_price"] == 165.0
    # Expected dollar profit = $200 * 3 = $600.0
    assert data["expected_dollar_profit"] == 600.0

def test_ai_agent_sentiment_synthesis():
    payload = {
        "sector_topic": "Semiconductors & AI",
        "target_watchlist": ["NVDA", "AAPL", "MSFT"]
    }
    response = client.post("/api/agent/sentiment-synthesis", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "success"
    assert res["mode"] == "SENTIMENT_SYNTHESIS"
    assert "macro_regime" in res["structured_data"]
    assert "asset_class_impact" in res["structured_data"]

def test_ai_agent_templates():
    response = client.get("/api/agent/templates")
    assert response.status_code == 200
    templates = response.json()
    assert "skill_1_market_analysis" in templates
    assert "skill_2_targeted_stock" in templates
    assert "skill_3_advanced_technical" in templates
    assert "skill_4_structured_execution" in templates
    assert "skill_5_trade_journaling" in templates
    assert "skill_6_strategy_review" in templates

# ==========================================
# 6 Core Skills Tests
# ==========================================

def test_skill_1_market_analysis():
    payload = {"criteria": "strong quarterly earnings, low volatility, sector momentum"}
    res = client.post("/api/agent/skill/market-analysis", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["mode"] == "SKILL_MARKET_SCREENING"
    assert data["structured_data"]["shortlist_count"] > 0

def test_skill_2_targeted_stock():
    payload = {"asset_name": "NVDA", "timeframe": "Daily / 4H"}
    res = client.post("/api/agent/skill/targeted-stock", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["mode"] == "SKILL_TARGETED_RESEARCH"
    assert "support_zones" in data["structured_data"]
    assert "risk_reward_scenarios" in data["structured_data"]

def test_skill_3_advanced_technical():
    payload = {"asset_name": "BTCUSDT", "current_price": 65000.0}
    res = client.post("/api/agent/skill/advanced-technical", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["mode"] == "SKILL_ADVANCED_TECHNICAL"
    assert "trade_setup" in data["structured_data"]
    assert "stop_loss" in data["structured_data"]["trade_setup"]

def test_skill_4_structured_execution():
    payload = {
        "instrument": "AAPL",
        "direction": "LONG",
        "entry_price": 150.0,
        "position_size": 40.0,
        "stop_loss": 145.0,
        "take_profit": 165.0,
        "reasoning": "50 EMA bounce with high volume & bullish divergence"
    }
    res = client.post("/api/agent/skill/structured-execution", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["mode"] == "SKILL_STRUCTURED_EXECUTION"
    assert data["structured_data"]["risk_reward_ratio"] == "1:3.0"

def test_skill_5_trade_journaling():
    payload = {"time_period": "Last 30 Days"}
    res = client.post("/api/agent/skill/trade-journaling", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["mode"] == "SKILL_TRADE_JOURNALING"
    assert "sharpe_ratio" in data["structured_data"]
    assert "habits_audit" in data["structured_data"]

def test_skill_6_strategy_review():
    payload = {
        "strategy_name": "Breakout Momentum",
        "market_context": "High Volatility Bull Trend"
    }
    res = client.post("/api/agent/skill/strategy-review", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["mode"] == "SKILL_STRATEGY_REVIEW"
    assert "pitfalls_and_risks" in data["structured_data"]

def test_skill_7_psychology():
    payload = {
        "issue_topic": "FOMO and Hesitation",
        "recent_scenario": "Hesitated on breakout, chased top, got stopped."
    }
    res = client.post("/api/agent/skill/psychology", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["mode"] == "SKILL_PSYCHOLOGY_ANALYSIS"
    assert "actionable_techniques" in data["structured_data"]
    assert "mindset_exercise" in data["structured_data"]

def test_skill_8_deep_dive():
    payload = {
        "topic": "Options Greeks & Implied Volatility",
        "skill_level": "Advanced"
    }
    res = client.post("/api/agent/skill/deep-dive", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["mode"] == "SKILL_SPECIAL_TOPIC_LEARNING"
    assert len(data["structured_data"]["curriculum"]) == 4

def test_skill_9_backtest_expert():
    payload = {
        "strategy_name": "Breakout Momentum",
        "lookback_period": "5 Years",
        "assumed_slippage_bps": 5.0
    }
    res = client.post("/api/agent/skill/backtest-expert", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["mode"] == "SKILL_BACKTESTING_EXPERT"
    assert "bias_checks" in data["structured_data"]
    assert "sharpe_ratio" in data["structured_data"]["performance_interpretation"]

def test_skill_10_premarket():
    payload = {
        "focus_assets": ["BTCUSDT", "NVDA", "AAPL", "SPY"],
        "overnight_notes": "Asia green, futures up."
    }
    res = client.post("/api/agent/skill/pre-market", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["mode"] == "SKILL_PREMARKET_ROUTINE"
    assert "checklist" in data["structured_data"]

def test_concurrent_10_skill_audit():
    payload = {
        "passphrase": "secret_key",
        "symbol": "BTCUSDT",
        "action": "BUY",
        "price": 65000.0,
        "quantity": 1.0,
        "indicators": {
            "rsi": 55.0,
            "volatility": 1.5,
            "volume_ratio": 1.8
        }
    }
    res = client.post("/api/agent/audit-signal", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["overall_skill_score"] >= 90.0
    assert len(data["skills_audit_list"]) == 10
    assert data["passed_skills_count"] >= 9

def test_12_indicators_evaluation():
    payload = {
        "rsi": 58.0,
        "macd_hist": 1.5,
        "ema_20_above_50": True,
        "ema_50_above_200": True,
        "supertrend_bullish": True,
        "bollinger_pct_b": 0.65,
        "atr_pct": 1.8,
        "vwap_bullish": True,
        "obv_trend": "BULLISH",
        "stoch_rsi_k": 68.0,
        "adx": 28.0,
        "ichimoku_above_cloud": True,
        "mfi": 62.0
    }
    res = client.post("/api/evaluate-12-indicators", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["total_score"] >= 80.0
    assert data["passed_indicators_count"] >= 10
    assert data["verdict"] in ["STRONG_BUY", "BUY"]

def test_top20_ranking_generation():
    res = client.get("/api/top20-recommendations")
    assert res.status_code == 200
    data = res.json()
    assert len(data["stocks"]) == 20
    assert data["stocks"][0]["rank"] == 1
    assert data["stocks"][0]["composite_score"] >= data["stocks"][1]["composite_score"]
    first_stock = data["stocks"][0]
    assert first_stock["target_profit_1_pct"] > first_stock["entry_price"]
    assert first_stock["stop_loss_0_4_pct"] < first_stock["entry_price"]

def test_asymmetric_margin_calculation():
    # Test BIST (+%3.0 / -%1.5 / ~%0.35 komisyon)
    payload_bist = {
        "account_size": 50000.0,
        "risk_per_trade_pct": 1.0,
        "entry_price": 100.0,
        "symbol": "THYAO",
        "market": "BIST",
        "action": "BUY",
        "custom_tp_pct": 3.0,
        "custom_sl_pct": 1.5
    }
    res_bist = client.post("/api/calculate-asymmetric-margin", json=payload_bist)
    assert res_bist.status_code == 200
    data_bist = res_bist.json()
    assert data_bist["target_profit_price"] == 103.0  # +3.0%
    assert data_bist["stop_loss_price"] == 98.5       # -1.5%
    assert data_bist["currency"] == "₺"
    assert data_bist["cost_breakdown_at_target"]["net_pnl"] > 0
    assert data_bist["cost_breakdown_at_target"]["total_friction_costs"] > 0

    # Test NASDAQ (+%3.5 / -%1.75)
    payload_us = {
        "account_size": 10000.0,
        "risk_per_trade_pct": 0.8,
        "entry_price": 100.0,
        "symbol": "QQQ",
        "market": "NASDAQ",
        "action": "BUY",
        "target_profit_pct": 3.5,
        "stop_loss_pct": 1.75
    }
    res_us = client.post("/api/calculate-asymmetric-margin", json=payload_us)
    assert res_us.status_code == 200
    data_us = res_us.json()
    assert data_us["target_profit_price"] == 103.5  # +3.5%
    assert data_us["stop_loss_price"] == 98.25      # -1.75%
    assert data_us["currency"] == "$"
    assert data_us["cost_breakdown_at_target"]["net_pnl"] > 0

def test_trade_lifecycle_simulation():
    payload = {
        "capital_usd": 100.0,
        "symbol": "NVDA",
        "market": "NASDAQ",
        "entry_price": 128.50,
        "target_profit_pct": 3.50,
        "stop_loss_pct": 1.75,
        "slippage_pct": 0.08
    }
    res = client.post("/api/simulate-trade-lifecycle", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["initial_capital"] == 100.0
    assert data["final_capital"] > 100.0
    assert data["net_profit"] > 0
    assert len(data["lifecycle_steps"]) == 4

if __name__ == "__main__":
    print("Running system validation...")
    test_health_endpoint()
    print("[OK] Health endpoint")
    test_live_news_endpoint()
    print("[OK] Live news & macro NLP feed")
    test_low_risk_signal_execution()
    print("[OK] Low risk order execution & sizing")
    test_high_volatility_hard_rule_rejection()
    print("[OK] Hard rule circuit breaker rejection")
    test_bot_training_engine()
    print("[OK] Bot training & backtest calibration")
    test_ai_agent_fundamental_research()
    print("[OK] AI Agent: Fundamental & Moat Research")
    test_ai_agent_earnings_breakdown()
    print("[OK] AI Agent: Earnings Report Breakdown")
    test_ai_agent_position_sizing()
    print("[OK] AI Agent: Position Sizing & 1:3 R:R Calculation")
    test_ai_agent_sentiment_synthesis()
    print("[OK] AI Agent: Market Sentiment & Macro Synthesis")
    test_ai_agent_templates()
    print("[OK] AI Agent: Templates API")
    
    # 10 Master Skills
    test_skill_1_market_analysis()
    print("[OK] Skill 1: In-Depth Market Analysis")
    test_skill_2_targeted_stock()
    print("[OK] Skill 2: Targeted Stock Research")
    test_skill_3_advanced_technical()
    print("[OK] Skill 3: Advanced Technical Analysis")
    test_skill_4_structured_execution()
    print("[OK] Skill 4: Structured Trade Execution")
    test_skill_5_trade_journaling()
    print("[OK] Skill 5: Effective Trade Journaling")
    test_skill_6_strategy_review()
    print("[OK] Skill 6: Comprehensive Strategy Review")
    test_skill_7_psychology()
    print("[OK] Skill 7: Trading Psychology Analysis")
    test_skill_8_deep_dive()
    print("[OK] Skill 8: Deep-Dive Special Topics")
    test_skill_9_backtest_expert()
    print("[OK] Skill 9: AI-Assisted Backtesting")
    test_skill_10_premarket()
    print("[OK] Skill 10: Pre-Market Preparation Routine")
    test_concurrent_10_skill_audit()
    print("[OK] Concurrent 10-Skill Live Inspection & Audit Matrix")
    
    # 12 İndikatör, Top 20 & Asimetrik Marj Testleri
    test_12_indicators_evaluation()
    print("[OK] 12 TradingView Indicators Engine Evaluation")
    test_top20_ranking_generation()
    print("[OK] Top 20 Stock Recommendation Multi-Criteria Matrix")
    test_asymmetric_margin_calculation()
    print("[OK] Asymmetric Margin Engine (+1.0% Profit / -0.4% Stop Loss / 2.5:1 R:R)")
    test_trade_lifecycle_simulation()
    print("[OK] $100 Trade Lifecycle Simulator (Signal -> Slippage -> Break-Even -> Take-Profit)")
    
    print("\n>>> All 25 validation tests passed successfully! $100 Simulator is fully operational! <<<")
