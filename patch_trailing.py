import sys

with open('services/market_feed/live_stream.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Modify the market hours check
old_market_check = '''            try:
                from services.risk_engine.market_hours import market_hours_validator
                is_open, _, _ = market_hours_validator.is_market_open(pos.symbol)
                if not is_open:
                    continue
            except Exception:
                pass'''
new_market_check = '''            is_open = True
            try:
                from services.risk_engine.market_hours import market_hours_validator
                is_open, _, _ = market_hours_validator.is_market_open(pos.symbol)
            except Exception:
                pass'''
code = code.replace(old_market_check, new_market_check)

# 2. Add is_open condition to close_position for TP/SL (BUY)
old_buy_tp = '''                if curr_price >= pos.target_profit_price:
                    self.close_position(pos_id, "CLOSED_TP")
                    continue'''
new_buy_tp = '''                if curr_price >= pos.target_profit_price:
                    if is_open:
                        self.close_position(pos_id, "CLOSED_TP")
                        continue'''
code = code.replace(old_buy_tp, new_buy_tp)

old_buy_sl = '''                    reason = "CLOSED_TRAILING" if pos.trailing_stop_activated else "CLOSED_SL"
                    self.close_position(pos_id, reason)
                    continue'''
new_buy_sl = '''                    if is_open:
                        reason = "CLOSED_TRAILING" if pos.trailing_stop_activated else "CLOSED_SL"
                        self.close_position(pos_id, reason)
                        continue'''
code = code.replace(old_buy_sl, new_buy_sl)

# 3. Add is_open condition to close_position for TP/SL (SELL)
old_sell_tp = '''                if curr_price <= pos.target_profit_price:
                    self.close_position(pos_id, "CLOSED_TP")
                    continue'''
new_sell_tp = '''                if curr_price <= pos.target_profit_price:
                    if is_open:
                        self.close_position(pos_id, "CLOSED_TP")
                        continue'''
code = code.replace(old_sell_tp, new_sell_tp)

old_sell_sl = '''                    reason = "CLOSED_TRAILING" if pos.trailing_stop_activated else "CLOSED_SL"
                    self.close_position(pos_id, reason)
                    continue'''
code = code.replace(old_sell_sl, new_buy_sl) # Reusing the new_buy_sl block

# 4. Add is_open condition to FLASH CRASH (BUY)
old_buy_flash = '''                if pct <= -3.0 and not pos.trailing_stop_activated:
                    logger.warning(f"🚨 [FLASH CRASH DETECTED] {pos.symbol} %{pct:.2f} düştü! Acil stop tetikleniyor.")
                    self.close_position(pos_id, "CLOSED_FLASH_CRASH")
                    continue'''
new_buy_flash = '''                if pct <= -3.0 and not pos.trailing_stop_activated:
                    if is_open:
                        logger.warning(f"🚨 [FLASH CRASH DETECTED] {pos.symbol} %{pct:.2f} düştü! Acil stop tetikleniyor.")
                        self.close_position(pos_id, "CLOSED_FLASH_CRASH")
                        continue'''
code = code.replace(old_buy_flash, new_buy_flash)

# 5. Make Trailing Stop Distances MORE DYNAMIC (BUY)
old_buy_dist = '''                if pct > 5.0:
                    trailing_dist = 0.99  # %1 izleme (çok kârda, sıkı takip)
                elif pct > 2.5:
                    trailing_dist = 0.985 # %1.5 izleme
                elif pct > 1.0:
                    trailing_dist = max(0.99, base_dist + 0.005) # Kâra geçince daralt
                else:
                    trailing_dist = base_dist # Orijinal SL veya 2-3%'''
new_buy_dist = '''                if pct > 4.0:
                    trailing_dist = 0.995 # %0.5 makas!
                elif pct > 2.0:
                    trailing_dist = 0.992 # %0.8 makas!
                elif pct > 1.0:
                    trailing_dist = 0.988 # %1.2 makas!
                elif pct > 0.5:
                    trailing_dist = 0.985 # %1.5 makas
                else:
                    trailing_dist = base_dist'''
code = code.replace(old_buy_dist, new_buy_dist)

# 6. Make Trailing Stop Distances MORE DYNAMIC (SELL)
old_sell_dist = '''                if pct > 5.0:
                    trailing_dist = 1.01  # %1 izleme
                elif pct > 2.5:
                    trailing_dist = 1.015 # %1.5 izleme
                elif pct > 1.0:
                    trailing_dist = min(1.01, base_dist - 0.005)
                else:
                    trailing_dist = base_dist'''
new_sell_dist = '''                if pct > 4.0:
                    trailing_dist = 1.005 # %0.5 makas!
                elif pct > 2.0:
                    trailing_dist = 1.008 # %0.8 makas!
                elif pct > 1.0:
                    trailing_dist = 1.012 # %1.2 makas!
                elif pct > 0.5:
                    trailing_dist = 1.015 # %1.5 makas
                else:
                    trailing_dist = base_dist'''
code = code.replace(old_sell_dist, new_sell_dist)

with open('services/market_feed/live_stream.py', 'w', encoding='utf-8') as f:
    f.write(code)

print('Success!')
