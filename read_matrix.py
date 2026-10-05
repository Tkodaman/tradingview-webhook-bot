import json

with open('matrix2.json', 'r', encoding='utf-16') as f:
    d = json.load(f)

items = sorted(d.get('items', []), key=lambda x: x.get('confidence_score', 0), reverse=True)

for i in items[:15]:
    sym = i.get('symbol', 'N/A')
    score = i.get('confidence_score', 0)
    vol = i.get('volume_ratio', 0)
    rsi = i.get('rsi', 0)
    change = i.get('change_pct', 0)
    reason = i.get('reason', '')
    print(f"{sym:<10} | Score: {score:>5.1f} | Vol: {vol:>4.2f}x | RSI: {rsi:>5.1f} | Chg: {change:>5.2f}% | {reason}")
