import asyncio
import websockets
import json

async def test():
    async with websockets.connect('ws://127.0.0.1:8000/ws/live') as ws:
        msg = await ws.recv()
        data = json.loads(msg)
        print("WS Message keys:", data.keys())
        if data.get("type") == "LIVE_MARKET":
            print("Summary:", data["data"]["summary"])

asyncio.run(test())
