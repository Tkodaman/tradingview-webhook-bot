import sys
import os

# Proje kök dizinini sys.path'e ekle (doğrudan alt klasörden çalıştırılsa bile modül hatasını önler)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from services.ai_agent.research_engine import financial_agent
from services.ai_agent.prompts import (
    SYSTEM_ANALYST_PROMPT,
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

__all__ = [
    "financial_agent",
    "SYSTEM_ANALYST_PROMPT",
    "FUNDAMENTAL_RESEARCH_TEMPLATE",
    "EARNINGS_BREAKDOWN_TEMPLATE",
    "POSITION_SIZING_TEMPLATE",
    "SENTIMENT_SYNTHESIS_TEMPLATE",
    "SKILL_MARKET_ANALYSIS_TEMPLATE",
    "SKILL_TARGETED_STOCK_TEMPLATE",
    "SKILL_ADVANCED_TECHNICAL_TEMPLATE",
    "SKILL_STRUCTURED_EXECUTION_TEMPLATE",
    "SKILL_TRADE_JOURNALING_TEMPLATE",
    "SKILL_STRATEGY_REVIEW_TEMPLATE",
    "SKILL_PSYCHOLOGY_ANALYSIS_TEMPLATE",
    "SKILL_SPECIAL_TOPIC_LEARNING_TEMPLATE",
    "SKILL_BACKTESTING_EXPERT_TEMPLATE",
    "SKILL_PREMARKET_ROUTINE_TEMPLATE"
]

if __name__ == "__main__":
    print("[OK] AI Agent module initialized successfully.")
