import asyncio
from dotenv import load_dotenv
load_dotenv()

from routers.position_router import open_live_position, OpenPositionRequest

async def test_endpoint():
    req = OpenPositionRequest(symbol="UNIUSDT", capital=100.0, side="BUY", tp_pct=3.0, sl_pct=1.5)
    try:
        res = await open_live_position(req)
        print("Success:", res)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_endpoint())
