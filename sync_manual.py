import sys
import uuid
from datetime import datetime, timezone
import pytz

sys.path.append("c:\\Users\\ASUS\\OneDrive\\Desktop\\tradingview-webhook-bot")
from services.market_feed.live_stream import live_trade_manager, ActivePosition

def sync_position(symbol, entry_price, nominal_value, side="BUY"):
    TRT = pytz.timezone("Europe/Istanbul")
    now_str = datetime.now(TRT).strftime("%Y-%m-%d %H:%M:%S")
    pos_id = f"{symbol}-{uuid.uuid4().hex[:6]}"
    
    # Calculate quantity
    qty = nominal_value / entry_price if entry_price > 0 else 0
    
    pos = ActivePosition(
        id=pos_id,
        symbol=symbol,
        side=side,
        entry_price=entry_price,
        current_price=entry_price,
        quantity=qty,
        nominal_value=nominal_value,
        opened_at=now_str,
        status="OPEN",
        highest_price=entry_price,
        lowest_price=entry_price,
        take_profit_price=entry_price * 1.10,  # default +10%
        stop_loss_price=entry_price * 0.95,    # default -5%
        target_profit_price=entry_price * 1.05,
        break_even_trigger_price=entry_price * 1.02,
        market="CRYPTO",
        source="MANUAL_SYNC"
    )
    
    # Clear old manually synced position for this symbol to avoid duplicates
    to_remove = [pid for pid, p in live_trade_manager.positions.items() if p.symbol == symbol]
    for pid in to_remove:
        del live_trade_manager.positions[pid]
        
    live_trade_manager.positions[pos_id] = pos
    live_trade_manager.save_state()
    print(f"OK Synced {symbol} - Entry: ${entry_price:.2f} - Nom: ${nominal_value:.2f}")

if __name__ == "__main__":
    usd_try_rate = 34.20
    
    # Midas
    sync_position("PLTR", 38.00, 500.0, "BUY")
    sync_position("NET",  80.00, 500.0, "BUY")
    sync_position("ANET", 400.00, 500.0, "BUY")
    sync_position("NVDA", 120.00, 500.0, "BUY")

    # BTCTurk (Converting TL to USD)
    sync_position("INJUSDT", 368.12 / usd_try_rate, 14450 / usd_try_rate, "BUY")
    sync_position("SUIUSDT", 58.91 / usd_try_rate,  43831 / usd_try_rate, "BUY")
    sync_position("FILUSDT", 52.65 / usd_try_rate,  27507 / usd_try_rate, "BUY")
    sync_position("NEARUSDT", 236.3 / usd_try_rate, 31629 / usd_try_rate, "BUY")

    print("All manual positions synced successfully!")
