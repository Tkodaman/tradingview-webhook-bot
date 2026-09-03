from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# Foundational Schemas
class FundamentalRequest(BaseModel):
    company_name: str
    ticker: str
    peers: Optional[List[str]] = Field(default_factory=list)
    custom_context: Optional[str] = None

class EarningsRequest(BaseModel):
    company_name: str
    ticker: Optional[str] = None
    eps_actual: Optional[float] = None
    eps_estimate: Optional[float] = None
    eps_description: Optional[str] = None
    revenue_actual: Optional[str] = None
    revenue_estimate: Optional[str] = None
    revenue_description: Optional[str] = None
    guidance: Optional[str] = None
    commentary_notes: Optional[str] = None
    stock_reaction: Optional[str] = None

class PositionSizeRequest(BaseModel):
    account_size: float = Field(default=10000.0, gt=0, description="Total account capital in USD")
    risk_pct_per_trade: float = Field(default=2.0, gt=0, le=100, description="Risk % per trade")
    entry_price: float = Field(gt=0, description="Entry price per share/unit")
    stop_loss_price: Optional[float] = Field(default=None, description="Exact stop loss price")
    stop_distance: Optional[float] = Field(default=None, description="Distance below entry price e.g. $5")
    risk_reward_ratio: float = Field(default=3.0, gt=0, description="Risk to Reward target (e.g. 3 for 1:3)")
    leverage: float = Field(default=1.0, ge=1.0, description="Trading leverage if applicable")

class SentimentSynthesisRequest(BaseModel):
    sector_topic: str = Field(description="e.g. Semiconductors, Tech, Oil & Gas, Crypto")
    target_watchlist: Optional[List[str]] = Field(default_factory=list, description="List of tickers")
    custom_headlines: Optional[List[str]] = Field(default_factory=list)

# Skills 1 to 6 Schemas
class MarketScreeningRequest(BaseModel):
    criteria: str = Field(default="strong quarterly earnings, low volatility, sector momentum", description="Screening criteria")
    universe: Optional[str] = "US Equities & Major Crypto"

class TargetedStockRequest(BaseModel):
    asset_name: str = Field(default="NVDA", description="Asset or Stock symbol/name")
    timeframe: Optional[str] = "Daily / 4H"
    recent_news: Optional[str] = None

class AdvancedTechnicalRequest(BaseModel):
    asset_name: str = Field(default="BTCUSDT", description="Asset ticker")
    current_price: Optional[float] = None
    indicators: Optional[Dict[str, float]] = Field(default_factory=dict)
    catalysts: Optional[str] = None

class StructuredExecutionRequest(BaseModel):
    trade_id: Optional[str] = None
    instrument: str = "AAPL"
    direction: str = Field(default="LONG", pattern="^(LONG|SHORT|BUY|SELL)$")
    entry_price: float
    exit_price: Optional[float] = None
    position_size: float
    stop_loss: float
    take_profit: float
    reasoning: str
    outcome: Optional[str] = "OPEN"
    timestamp: Optional[str] = None

class JournalingReviewRequest(BaseModel):
    time_period: str = Field(default="Last 30 Days", description="e.g. Last 30 Days, Q3 2026")
    trades_sample: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    initial_balance: Optional[float] = 10000.0

class StrategyReviewRequest(BaseModel):
    strategy_name: str = Field(default="Order Flow & Breakout Momentum", description="Strategy, tool, or market structure")
    market_context: Optional[str] = "High Volatility / Bull Market Trend"

# Skills 7 to 10 Schemas
class PsychologyAnalysisRequest(BaseModel):
    issue_topic: Optional[str] = Field(default="FOMO and Hesitation", description="e.g. FOMO, Overconfidence, Revenge Trading, Hesitation")
    recent_scenario: Optional[str] = "Hesitated to enter valid breakout, then chased at high price and got stopped out."

class SpecialTopicLearningRequest(BaseModel):
    topic: str = Field(default="Options & Implied Volatility Trading", description="e.g. Options Greek Hedging, Volatility Skew, Order Flow Imbalances")
    skill_level: Optional[str] = "Intermediate to Advanced"

class BacktestingExpertRequest(BaseModel):
    strategy_name: Optional[str] = "Volatility Breakout with Volume Confirmation"
    lookback_period: Optional[str] = "5 Years (2021-2026)"
    include_costs: Optional[bool] = True
    assumed_slippage_bps: Optional[float] = 5.0 # 5 basis points

class PreMarketRoutineRequest(BaseModel):
    trading_date: Optional[str] = None
    focus_assets: Optional[List[str]] = Field(default_factory=lambda: ["BTCUSDT", "NVDA", "AAPL", "SPY"])
    overnight_notes: Optional[str] = "Asia/Europe markets green, US futures +0.4%, Fed Chair speaks at 14:00."

class CustomAnalystRequest(BaseModel):
    prompt: str
    mode: Optional[str] = "GENERAL_ANALYST"
    symbol: Optional[str] = None

class AgentResponse(BaseModel):
    status: str = "success"
    mode: str
    title: str
    summary: str
    structured_data: Dict[str, Any]
    detailed_report: str
    actionable_takeaway: str
    suggested_risk_parameters: Optional[Dict[str, Any]] = None
