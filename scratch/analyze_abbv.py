import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.append(r'c:\Users\ASUS\OneDrive\Desktop\tradingview-webhook-bot')
from services.ai_agent.research_engine import FinancialResearchAgent, AdvancedTechnicalRequest

agent = FinancialResearchAgent()
req = AdvancedTechnicalRequest(asset='ABBV', current_price=262.08, timeframes=['15m', '1h', '4h'])
response = agent.advanced_technical_analysis(req)

with open(r'c:\Users\ASUS\OneDrive\Desktop\tradingview-webhook-bot\scratch\abbv_output.md', 'w', encoding='utf-8') as f:
    f.write(response.detailed_report)
