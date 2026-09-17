import os

with open('services/ai_agent/research_engine.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Add imports at the top
import_str = '''import math
import time
import os
from openai import OpenAI'''
code = code.replace('''import math\nimport time''', import_str)

# 2. Add __init__ to FinancialResearchAgent
init_str = '''class FinancialResearchAgent:
    """
    Wall Street Düzeyinde 10-Skill Master AI Finansal Analiz & İşlem Ajanı
    """

    execution_journal_db: List[Dict[str, Any]] = []

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4o")
        
        self.client = None
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            
    def _query_openai(self, prompt: str, system_msg: str = "Sen kıdemli bir Wall Street kantitatif analistisin. Çok net, profesyonel ve teknik Türkçe konuşursun.") -> str:
        if not self.client:
            return "Sistem Hatası: OpenAI API Key bulunamadı."
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API Hatası: {str(e)}")
            return f"Üzgünüm, analiz motoru yanıt veremedi: {str(e)}"
'''
code = code.replace('''class FinancialResearchAgent:
    """
    Wall Street Düzeyinde 10-Skill Master AI Finansal Analiz & İşlem Ajanı
    """

    execution_journal_db: List[Dict[str, Any]] = []''', init_str)

# 3. Rewrite ask_custom_analyst
old_ask = '''    def ask_custom_analyst(self, req: CustomAnalystRequest) -> AgentResponse:
        try:
            p = req.prompt.lower()
            if "psychology" in p or "fomo" in p or "psikoloji" in p or "hesitation" in p:
                return self.analyze_trading_psychology(PsychologyAnalysisRequest(issue_topic=req.prompt))
            elif "learn" in p or "mentor" in p or "options" in p or "öğren" in p:
                return self.learn_special_topic(SpecialTopicLearningRequest(topic=req.symbol or "Options Trading"))
            elif "backtest" in p or "slippage" in p or "overfitting" in p:
                return self.expert_backtesting_guidance(BacktestingExpertRequest(strategy_name=req.symbol or "Momentum Strategy"))
            elif "pre-market" in p or "premarket" in p or "hazırlık" in p or "checklist" in p:
                return self.generate_premarket_routine(PreMarketRoutineRequest())
            elif "screen" in p or "tarama" in p:
                return self.screen_market_assets(MarketScreeningRequest(criteria=req.prompt))
            elif "price and volume" in p or "hedef" in p:
                return self.research_targeted_stock(TargetedStockRequest(asset_name=req.symbol or "NVDA"))
            elif "technical" in p or "teknik" in p:
                return self.advanced_technical_analysis(AdvancedTechnicalRequest(asset_name=req.symbol or "BTCUSDT"))
            elif "execution" in p or "log" in p:
                return self.structured_trade_execution(StructuredExecutionRequest(instrument=req.symbol or "AAPL", direction="LONG", entry_price=150.0, position_size=10.0, stop_loss=145.0, take_profit=165.0, reasoning=req.prompt))
            elif "journal" in p or "sharpe" in p:
                return self.review_trade_journal(JournalingReviewRequest(time_period="Son 30 Gün"))
            elif "strategy" in p or "strateji" in p:
                return self.review_trading_strategy(StrategyReviewRequest(strategy_name=req.symbol or "Breakout & Momentum"))
            elif "balance sheet" in p or "fundamental" in p:
                symbol = req.symbol or "AAPL"
                return self.analyze_fundamentals(FundamentalRequest(company_name=symbol, ticker=symbol))
            elif "earnings" in p or "bilanço" in p:
                symbol = req.symbol or "NVDA"
                return self.breakdown_earnings(EarningsRequest(company_name=symbol, ticker=symbol))
            elif "risk" in p or "position size" in p:
                return self.calculate_position_size(PositionSizeRequest(account_size=10000.0, risk_pct_per_trade=2.0, entry_price=100.0, stop_distance=5.0, risk_reward_ratio=3.0))
            else:
                return self.synthesize_market_sentiment(SentimentSynthesisRequest(sector_topic=req.symbol or "Technology & AI"))
        except Exception as e:
            logger.error(f"LLM Agent Engine Error: {str(e)}. Using fallback response.")
            return self.fallback_cached_response(req)'''

new_ask = '''    def ask_custom_analyst(self, req: CustomAnalystRequest) -> AgentResponse:
        try:
            # Doğrudan kullanıcının sorusunu OpenAI'ye yönlendir
            system_msg = "Sen elit bir kantitatif analist ve trade psikoloğusun. Adın Gölge Zeka. Gelen sorulara profesyonel, doğrudan ve eyleme dökülebilir (actionable) Türkçe yanıtlar ver. Çok uzatma, net ol."
            
            # OpenAI isteği
            llm_response = self._query_openai(prompt=req.prompt, system_msg=system_msg)
            
            return AgentResponse(
                agent_name="Gölge Zeka (LLM Mode)",
                skill_used="Dynamic ChatGPT Analyst",
                mode="LIVE_LLM",
                title=f"Analiz: {req.symbol if req.symbol else 'Genel Piyasa'}",
                summary="Canlı LLM yanıtı oluşturuldu.",
                structured_data={"provider": "OpenAI/Astra"},
                detailed_report=f"### 🤖 Gerçek Zamanlı Analiz\\n\\n{llm_response}",
                actionable_takeaway="Önerileri kendi stratejinize göre filtreleyin."
            )
        except Exception as e:
            logger.error(f"LLM Agent Engine Error: {str(e)}. Using fallback response.")
            return self.fallback_cached_response(req)'''
code = code.replace(old_ask, new_ask)

with open('services/ai_agent/research_engine.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Patch applied to research_engine.py successfully.")
