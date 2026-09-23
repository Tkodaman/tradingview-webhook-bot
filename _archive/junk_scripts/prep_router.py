with open('routers/position_router.py', 'r', encoding='utf-8') as f:
    text = f.read()

# I need to find where active_list is populated in get_active_positions
# And inject the dynamic margin logic.

# In router.get("/active")
#                    if tp_price == 0.0 or sl_price == 0.0:
#                        if entry_price > 0:

import re

target_block = '''                    if tp_price == 0.0 or sl_price == 0.0:
                        if entry_price > 0:
                            from services.engine.experience_memory_engine import experience_memory_engine
                            dyn_tp_pct, dyn_sl_pct = experience_memory_engine.get_dynamic_margins(sym)
                            if side == "BUY":
                                tp_price = entry_price * (1.0 + (dyn_tp_pct / 100.0))
                                sl_price = entry_price * (1.0 - (dyn_sl_pct / 100.0))
                            else:
                                tp_price = entry_price * (1.0 - (dyn_tp_pct / 100.0))
                                sl_price = entry_price * (1.0 + (dyn_sl_pct / 100.0))'''

if 'dyn_tp_pct' not in text:
    # Let's search for stop_loss_price": 0.0,
    search_str = '''                        "target_profit_price": 0.0, # Alpaca RAW endpoint doesn't expose nested bracket prices directly in list_positions easily
                        "stop_loss_price": 0.0,'''
                        
    replace_str = '''                        "target_profit_price": round(tp_price, 4),
                        "stop_loss_price": round(sl_price, 4),'''
                        
    # Wait, we need to define tp_price and sl_price before active_list.append
    # Let's do a more robust regex replacement inside the for loop
    
    # We will find entry_price = float(p.get("avg_entry_price", 0)) and side = 
    
    # Actually, in the current file, it looks like:
    #                     "entry_price": float(p.get("avg_entry_price", 0)),
    #                     "current_price": float(p.get("current_price", 0)),
    
    pass

