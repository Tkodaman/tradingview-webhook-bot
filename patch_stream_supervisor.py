with open('services/market_feed/live_stream.py', 'r', encoding='utf-8') as f:
    text = f.read()
import re

# 1. Budget multiplier integration
new_budget = '''
    def get_dynamic_position_capital(self, symbol: str) -> float:
        """
        Kasa Bakiyesine Göre Dinamik Pozisyon Bütçesi (%10 Taban = ) + Süpervizör Risk Çarpanı
        """
        try:
            from services.engine.supervisor_agent import supervisor_agent
            multiplier = supervisor_agent.calculate_dynamic_budget_multiplier(self.market_prices)
        except ImportError:
            multiplier = 1.0
            
        base_capital = round(self.total_account_equity * 0.10, 2)
        adjusted_capital = base_capital * multiplier
        
        # En az 10$, en fazla bakiyenin %25'i kadar
        return max(10.0, min(adjusted_capital, self.total_account_equity * 0.25))
'''
text = re.sub(
    r'def get_dynamic_position_capital\(self, symbol: str\) -> float:.*?(?=\n\s*def |\Z)',
    new_budget.strip() + '\n\n',
    text,
    flags=re.DOTALL
)

# 2. Record Trade Result
new_close = '''
        if gross is not None:
            self.realized_pnl += gross
            try:
                from services.engine.supervisor_agent import supervisor_agent
                supervisor_agent.record_trade_result(gross, pos.symbol)
            except ImportError:
                pass

        pos.status = "CLOSED"
        pos.close_reason = reason
'''
text = re.sub(
    r'if gross is not None:\s*self\.realized_pnl \+= gross\s*pos\.status = "CLOSED"\s*pos\.close_reason = reason',
    new_close.strip(),
    text,
    flags=re.DOTALL
)

# 3. Fix Alpaca Sync Dictionary AttributeError
new_alpaca_sync = '''
                alpaca_symbols = set()
                for ap in alpaca_positions:
                    sym = ap.get("symbol") if isinstance(ap, dict) else getattr(ap, "symbol", None)
                    if not sym: continue
                    alpaca_symbols.add(sym)
                    
                    local_match = next((p for p in self.positions.values() if p.symbol == sym and p.status == "OPEN"), None)
                    if not local_match:
                        from services.order_router import ActivePosition
                        pos_id = f"POS_{int(time.time()*1000)}_{sym}"
                        entry_price = float(ap.get("avg_entry_price") if isinstance(ap, dict) else getattr(ap, "avg_entry_price", 0))
                        qty = float(ap.get("qty") if isinstance(ap, dict) else getattr(ap, "qty", 0))
'''
text = re.sub(
    r'alpaca_symbols = set\(\)\s*for ap in alpaca_positions:\s*sym = ap\.symbol\s*alpaca_symbols\.add\(sym\)\s*local_match = next\(\(p for p in self\.positions\.values\(\) if p\.symbol == sym and p\.status == "OPEN"\), None\)\s*if not local_match:\s*from services\.order_router import ActivePosition\s*pos_id = f"POS_\{int\(time\.time\(\)\*1000\)\}_\{sym\}"\s*entry_price = float\(ap\.avg_entry_price\)\s*qty = float\(ap\.qty\)',
    new_alpaca_sync.strip(),
    text,
    flags=re.DOTALL
)

with open('services/market_feed/live_stream.py', 'w', encoding='utf-8') as f:
    f.write(text)
