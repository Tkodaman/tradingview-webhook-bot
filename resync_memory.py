import asyncio
from services.broker.factory import get_broker
from services.market_feed.live_stream import live_trade_manager
from services.engine.ha_manager import ha_manager

def resync_brokers():
    print("Mevcut brokerlarla senkronizasyon baslatiliyor...")
    try:
        # Zorla Lider yap ki sync calsin
        ha_manager.is_leader = True
        print("Botun ana hafizasi (LiveTradeManager) uzerinden senkronizasyon tetikleniyor...")
        live_trade_manager.sync_with_broker()
        print("Senkronizasyon tamamlandi. Su anki hafiza durumu:")
        
        count = 0
        for p in live_trade_manager.positions.values():
            if p.status in ["OPEN", "PENDING_BROKER"]:
                print(f"[{p.market}] {p.symbol}: {p.status} (Entry: {p.entry_price}, Qty: {p.quantity})")
                count += 1
        print(f"Toplam Aktif Pozisyon: {count}")
                
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    resync_brokers()
