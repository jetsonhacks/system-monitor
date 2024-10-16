from fasthtml.common import *
from starlette.websockets import WebSocket
from data_app import MODEL_NAME, get_gpu_load
import asyncio
import json

active_connections = set()

# This script is the websocket code for the client browser
# Double curly braces are used in the f-string to escape { } characters
# statusElement is the div which tells if the client is disconnected
data_update_websocket_script = """
<script>

    const statusElement = document.getElementById('connection-status');
    const gpuLoad = document.getElementById('gpu_load');
    const ws = new WebSocket('ws://127.0.0.1:5000/update-data');
    
    ws.onmessage = function(event) {
        const data = event.data;
        try {
            // Parse the incoming data and update the UI
            const eventData = JSON.parse(event.data);
            gpuLoad.innerText = eventData.gpu_load;
        }catch (error) {
            console.error("Failed to parse incoming data:", error);
        }
    };

    ws.onopen = function(event) {
        console.log("WebSocket connection established.");
        statusElement.style.display = "none";
    };

    ws.onclose = function(event) {
        console.log("WebSocket connection closed.");
        statusElement.innerText = "Disconnected";
        statusElement.style.color = "lightslategrey";
        statusElement.style.display = "block";
    };

    ws.onerror = function(event) {
        console.error("WebSocket error:", event);
        statusElement.innerText = "Connection Error";
        statusElement.style.color = "orange";
        statusElement.style.display = "block";
    };
</script>
"""

# Read the GPU usage and gather the rest of the system statistics
async def update_data():
    while True:
        gpu_load = get_gpu_load()
        # Tell the fans!
        for connection in list(active_connections):
            await connection.send_text(json.dumps({"gpu_load": gpu_load}))
        # Sleep asynchronously for 1 second
        await asyncio.sleep(1)

app, rt = fast_app()

@rt('/')
def get():
    gpu_load = get_gpu_load()
    page = Title('Jetson Web Sample'), Body(
        Div( H3(MODEL_NAME), 
            Span(f"GPU Load: "),
            Span(f"{gpu_load}", id="gpu_load"),
            Span("%"),
            style="text-align: center;"),
        Div("Disconnected", id="connection-status", cls="connection-status"),
        NotStr(data_update_websocket_script)
    )
    return page

# Websocket endpoint of update-data
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("New client connected.")
    active_connections.add(websocket)
    try:
        # The endpoint now just waits for the client to send messages
        while True:
            data = await websocket.receive_text()
            print(f"Message from client: {data}")
            # await websocket.send_text(f"Server echo: {data}")
    except Exception as e:
        print(f"WebSocket connection closed: {e}")
    finally:
        print("Client disconnected.")
        if websocket in active_connections:
            active_connections.remove(websocket)

app.routes.append(WebSocketRoute('/update-data', websocket_endpoint))

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(update_data())

if __name__ == "__main__":
    serve(host='0.0.0.0',port=5000)