import asyncio
import websockets

async def test_ws():
    try:
        async with websockets.connect("ws://localhost:8000/live") as websocket:
            print("Connected to WebSocket!")
            
            try:
                msg = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                print("Received message:")
                print(msg[:500])
            except asyncio.TimeoutError:
                print("No message received within 3 seconds.")
    except Exception as e:
        print("WebSocket Error:", e)

asyncio.run(test_ws())
