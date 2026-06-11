import asyncio
import json
import websockets

async def handler(ws):
    print("Client connected")
    try:
        async for message in ws:
            print("\n=== WebSocket message received ===")
            try:
                data = json.loads(message)
                print(json.dumps(data, indent=2))
            except Exception:
                print(message)
    except websockets.ConnectionClosed:
        print("Client disconnected")

async def main():
    server = await websockets.serve(handler, "localhost", 8765)
    print("WebSocket server listening at ws://localhost:8765")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())