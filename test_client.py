import asyncio
from services.data_ingestion.tradingview_live_client import tradingview_live_client

async def main():
    print("Testing TradingView Live Client Data Fetch...")
    data = await asyncio.to_thread(tradingview_live_client.fetch_live_market_data)
    print(f"Total symbols fetched: {len(data)}")
    
    nasdaq_count = sum(1 for v in data.values() if v.get("market") == "NASDAQ")
    bist_count = sum(1 for v in data.values() if v.get("market") == "BIST")
    crypto_count = sum(1 for v in data.values() if v.get("market") == "CRYPTO")
    
    print(f"NASDAQ Symbols: {nasdaq_count}")
    print(f"BIST Symbols: {bist_count}")
    print(f"CRYPTO Symbols: {crypto_count}")

    # Check volume ratios
    print("\nSample Volume Ratios:")
    for sym in ["NVDA", "THYAO", "BTCUSDT"]:
        if sym in data:
            item = data[sym]
            print(f"  {sym}: {item.get('volume_ratio')}x (Market: {item.get('market')})")
        else:
            print(f"  {sym}: Not found in data")

if __name__ == "__main__":
    asyncio.run(main())
