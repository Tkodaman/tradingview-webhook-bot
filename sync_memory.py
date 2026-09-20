import sqlite3, json, datetime
from collections import defaultdict

conn = sqlite3.connect('bot_database.db')
cursor = conn.cursor()
cursor.execute('SELECT * FROM trade_history ORDER BY id ASC')
rows = cursor.fetchall()
col_names = [d[0] for d in cursor.description]

mem = json.load(open('experience_memory.json', encoding='utf-8'))
mem['trade_history'] = []
mem['dynamic_clusters'] = {}
mem['asset_toxic_registry'] = {}
mem['learned_rules'] = []

for r in rows:
    t = dict(zip(col_names, r))
    # Fake values for missing fields required by memory engine
    is_win = float(t.get('net_pnl', 0)) > 0
    
    entry_pr = float(t.get('entry_price', 0))
    qty = float(t.get('quantity', 1.0))
    if qty <= 0: qty = 1.0
    nominal_value = entry_pr * qty
    
    pnl_pct = (float(t.get('net_pnl', 0)) / nominal_value) * 100 if nominal_value > 0 else 0
    win_str = "WIN" if is_win else "LOSS"
    # Add to memory
    mem['trade_history'].append({
        'trade_id': t['pos_id'],
        'symbol': t['symbol'],
        'action': t['side'],
        'entry_price': t['entry_price'],
        'exit_price': t['exit_price'],
        'pnl_amount': t['net_pnl'],
        'pnl_pct': pnl_pct,
        'is_win': is_win,
        'market_regime': 'NORMAL',
        'indicators_at_entry': {'market': 'CRYPTO', 'reason': t['reason']},
        'lesson_learned': f"{t['symbol']} {win_str}",
        'timestamp': t['closed_at'] or t['opened_at'],
        'duration_minutes': 15,
        'max_drawdown_percent': 0.0,
        'exit_reason': t['reason'],
        'error_margin_pct': 0.0,
        'algorithmic_action_plan': ''
    })

with open('experience_memory.json', 'w', encoding='utf-8') as f:
    json.dump(mem, f, indent=4)
print(f'Done! Synced {len(mem["trade_history"])} real trades to memory JSON.')
