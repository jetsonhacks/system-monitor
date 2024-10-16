import asyncio
import websockets

async def connect_to_websocket():
    uri = "ws://localhost:5000/update-data"
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket server")
            # Example of receiving messages in an infinite loop
            while True:
                data = await websocket.recv()
                print(f"Received data: {data}")
    except websockets.ConnectionClosed as e:
        print(f"Connection closed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(connect_to_websocket())
