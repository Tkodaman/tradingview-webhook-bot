with open('services/market_feed/live_stream.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
new_eval = '''
            pos.current_price = current_price
            
            # 1) Trailing & Breakeven Check
            try:
                from services.risk_engine.missing_agents import trailing_agent
                trailing_agent.evaluate_trailing(pos, current_price)
            except Exception as e:
                pass

            # 2) SL / TP Check
'''
text = re.sub(
    r'pos\.current_price = current_price\s*# Kâr/Zarar Limit Kontrolü',
    new_eval.strip() + '\n            # Kâr/Zarar Limit Kontrolü',
    text,
    flags=re.DOTALL
)

with open('services/market_feed/live_stream.py', 'w', encoding='utf-8') as f:
    f.write(text)
