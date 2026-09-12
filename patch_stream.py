with open('services/market_feed/live_stream.py', 'r', encoding='utf-8') as f:
    text = f.read()

new_sync = '''
    def sync_with_broker(self):
        from services.broker.alpaca_client import alpaca_client
        import time
        from datetime import datetime, timezone
        
        try:
            broker_positions = alpaca_client.sync_open_positions()
            if not broker_positions:
                return

            for bp in broker_positions:
                sym = bp.get("symbol")
                qty = abs(float(bp.get("qty", 0)))
                if qty == 0: continue
                
                # If we don't have it locally, add it
                if sym not in self.positions:
                    entry_price = float(bp.get("avg_entry_price", 0))
                    current_price = float(bp.get("current_price", entry_price))
                    side = "BUY" if float(bp.get("qty", 0)) > 0 else "SELL"
                    
                    # Estimate limits since broker might not return bracket details easily via /positions
                    tp_price = entry_price * 1.05 if side == "BUY" else entry_price * 0.95
                    sl_price = entry_price * 0.98 if side == "BUY" else entry_price * 1.02
                    
                    pos = ActivePosition(
                        id=f"sync_{int(time.time())}_{sym}",
                        symbol=sym,
                        market="NASDAQ",  # Defaulting to NASDAQ for Alpaca stocks
                        side=side,
                        entry_price=entry_price,
                        current_price=current_price,
                        quantity=qty,
                        nominal_value=entry_price * qty,
                        target_profit_price=tp_price,
                        stop_loss_price=sl_price,
                        break_even_trigger_price=entry_price * 1.02 if side == "BUY" else entry_price * 0.98,
                        opened_at=datetime.now(timezone.utc).isoformat(),
                        unrealized_pnl=float(bp.get("unrealized_pl", 0)),
                        unrealized_pnl_pct=float(bp.get("unrealized_plpc", 0)) * 100
                    )
                    self.positions[sym] = pos
            
            # Save the synced state to local db
            self.save_state()
        except Exception as e:
            from core.logger import logger
            logger.error(f"Failed to sync with broker: {e}")

    def load_state(self):
'''

text = text.replace("    def load_state(self):", new_sync.strip('\n'))

with open('services/market_feed/live_stream.py', 'w', encoding='utf-8') as f:
    f.write(text)
