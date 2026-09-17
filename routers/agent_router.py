from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from schemas.agent import (
    FundamentalRequest,
    EarningsRequest,
    PositionSizeRequest,
    SentimentSynthesisRequest,
    MarketScreeningRequest,
    TargetedStockRequest,
    AdvancedTechnicalRequest,
    StructuredExecutionRequest,
    JournalingReviewRequest,
    StrategyReviewRequest,
    PsychologyAnalysisRequest,
    SpecialTopicLearningRequest,
    BacktestingExpertRequest,
    PreMarketRoutineRequest,
    CustomAnalystRequest,
    AgentResponse
)
from services.ai_agent.research_engine import financial_agent
from services.ai_agent.prompts import (
    FUNDAMENTAL_RESEARCH_TEMPLATE,
    EARNINGS_BREAKDOWN_TEMPLATE,
    POSITION_SIZING_TEMPLATE,
    SENTIMENT_SYNTHESIS_TEMPLATE,
    SKILL_MARKET_ANALYSIS_TEMPLATE,
    SKILL_TARGETED_STOCK_TEMPLATE,
    SKILL_ADVANCED_TECHNICAL_TEMPLATE,
    SKILL_STRUCTURED_EXECUTION_TEMPLATE,
    SKILL_TRADE_JOURNALING_TEMPLATE,
    SKILL_STRATEGY_REVIEW_TEMPLATE,
    SKILL_PSYCHOLOGY_ANALYSIS_TEMPLATE,
    SKILL_SPECIAL_TOPIC_LEARNING_TEMPLATE,
    SKILL_BACKTESTING_EXPERT_TEMPLATE,
    SKILL_PREMARKET_ROUTINE_TEMPLATE
)
from schemas.webhook import WebhookSignal

router = APIRouter()

# ==========================================
# Foundational Endpoints
# ==========================================

@router.post("/fundamental", response_model=AgentResponse)
async def agent_fundamental_analysis(req: FundamentalRequest):
    return financial_agent.analyze_fundamentals(req)

@router.post("/earnings", response_model=AgentResponse)
async def agent_earnings_breakdown(req: EarningsRequest):
    return financial_agent.breakdown_earnings(req)

@router.post("/position-size", response_model=AgentResponse)
async def agent_position_sizing(req: PositionSizeRequest):
    return financial_agent.calculate_position_size(req)

@router.post("/sentiment-synthesis", response_model=AgentResponse)
async def agent_sentiment_synthesis(req: SentimentSynthesisRequest):
    return financial_agent.synthesize_market_sentiment(req)

# ==========================================
# 10 Core Master Trading Skills Endpoints
# ==========================================

@router.post("/skill/market-analysis", response_model=AgentResponse)
async def skill_market_analysis(req: MarketScreeningRequest):
    """1. In-Depth Market Analysis: Piyasa taraması ve fırsat kısa listesi"""
    return financial_agent.screen_market_assets(req)

@router.post("/skill/targeted-stock", response_model=AgentResponse)
async def skill_targeted_stock(req: TargetedStockRequest):
    """2. Targeted Stock Research: Fiyat/hacim gidişatı ve destek/direnç analizi"""
    return financial_agent.research_targeted_stock(req)

@router.post("/skill/advanced-technical", response_model=AgentResponse)
async def skill_advanced_technical(req: AdvancedTechnicalRequest):
    """3. Advanced Technical Analysis: Kesin giriş, stop-loss ve 1:3 kâr hedefleri"""
    return financial_agent.advanced_technical_analysis(req)

@router.post("/skill/structured-execution", response_model=AgentResponse)
async def skill_structured_execution(req: StructuredExecutionRequest):
    """4. Structured Trade Execution: Detaylı işlem icra kaydı ve önyargı önleme"""
    return financial_agent.structured_trade_execution(req)

@router.post("/skill/trade-journaling", response_model=AgentResponse)
async def skill_trade_journaling(req: JournalingReviewRequest):
    """5. Effective Trade Journaling: Sharpe, kazanma oranı, drawdown ve alışkanlık analizi"""
    return financial_agent.review_trade_journal(req)

@router.post("/skill/strategy-review", response_model=AgentResponse)
async def skill_strategy_review(req: StrategyReviewRequest):
    """6. Comprehensive Performance Review: Strateji mekaniği ve risk/tuzak incelemesi"""
    return financial_agent.review_trading_strategy(req)

@router.post("/skill/psychology", response_model=AgentResponse)
async def skill_psychology_analysis(req: PsychologyAnalysisRequest):
    """7. Trading Psychology Analysis: FOMO, aşırı güven ve tereddüt yönetimi"""
    return financial_agent.analyze_trading_psychology(req)

@router.post("/skill/deep-dive", response_model=AgentResponse)
async def skill_deep_dive_learning(req: SpecialTopicLearningRequest):
    """8. Deep-Dive Learning: Opsiyonlar ve volatilite gibi niş konularda derin mentorluk"""
    return financial_agent.learn_special_topic(req)

@router.post("/skill/backtest-expert", response_model=AgentResponse)
async def skill_backtest_expert(req: BacktestingExpertRequest):
    """9. AI-Assisted Backtesting: Slippage, overfitting denetimi ve metrik optimizasyonu"""
    return financial_agent.expert_backtesting_guidance(req)

@router.post("/skill/pre-market", response_model=AgentResponse)
async def skill_premarket_routine(req: PreMarketRoutineRequest):
    """10. Pre-Market Preparation Routine: Günlük hazırlık kontrol listesi ve seviyeler"""
    return financial_agent.generate_premarket_routine(req)

@router.post("/audit-signal")
async def audit_tradingview_signal(signal: WebhookSignal):
    """
    TradingView Sinyali ile Eş Zamanlı 10-Skill Denetim & Test Uç Noktası
    """
    return financial_agent.audit_tradingview_signal_concurrently(signal)

@router.post("/custom", response_model=AgentResponse)
async def agent_custom_prompt(req: CustomAnalystRequest):
    return financial_agent.ask_custom_analyst(req)

@router.get("/templates")
async def get_agent_templates():
    return {
        "fundamental": FUNDAMENTAL_RESEARCH_TEMPLATE,
        "earnings": EARNINGS_BREAKDOWN_TEMPLATE,
        "position_sizing": POSITION_SIZING_TEMPLATE,
        "sentiment_synthesis": SENTIMENT_SYNTHESIS_TEMPLATE,
        "skill_1_market_analysis": SKILL_MARKET_ANALYSIS_TEMPLATE,
        "skill_2_targeted_stock": SKILL_TARGETED_STOCK_TEMPLATE,
        "skill_3_advanced_technical": SKILL_ADVANCED_TECHNICAL_TEMPLATE,
        "skill_4_structured_execution": SKILL_STRUCTURED_EXECUTION_TEMPLATE,
        "skill_5_trade_journaling": SKILL_TRADE_JOURNALING_TEMPLATE,
        "skill_6_strategy_review": SKILL_STRATEGY_REVIEW_TEMPLATE,
        "skill_7_psychology": SKILL_PSYCHOLOGY_ANALYSIS_TEMPLATE,
        "skill_8_deep_dive": SKILL_SPECIAL_TOPIC_LEARNING_TEMPLATE,
        "skill_9_backtest_expert": SKILL_BACKTESTING_EXPERT_TEMPLATE,
        "skill_10_premarket": SKILL_PREMARKET_ROUTINE_TEMPLATE
    }


@router.get("/stream")
async def agent_custom_stream(prompt: str):
    """
    Sohbet penceresi için Streaming (Akış) endpoint'i.
    """
    def event_generator():
        try:
            # Sadece LLM kısmını stream et.
            for chunk in financial_agent._query_openai_stream(prompt=prompt):
                # SSE format: data: {text}


                # Encode newlines so they don't break SSE protocol
                safe_chunk = chunk.replace('\n', '<br>')
                yield f"data: {safe_chunk}\n\n"
        except Exception as e:
            yield f"data: Hata: {str(e)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
