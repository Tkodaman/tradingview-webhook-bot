import asyncio
from services.market_feed.live_stream import live_trade_manager

async def fix():
    live_trade_manager.load_state()
    pos = [p for p in live_trade_manager.positions.values() if p.symbol=='LINKUSD' and p.status=='OPEN']
    for p in pos:
        print("Closing:", p.id)
        live_trade_manager.close_position(p.id, 'SYNC_FIX')
    live_trade_manager.save_state()

if __name__ == "__main__":
    asyncio.run(fix())
