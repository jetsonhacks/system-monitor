from fasthtml.common import *
from starlette.websockets import WebSocket
from data_app import MODEL_NAME, get_gpu_load
import asyncio
import json

active_connections = set()

# Global variable to store the latest GPU load data
latest_data = {
    "gpu_percent": 0.0
}

def get_gpu_load_path():
    try:
        # Read the model name from /proc/device-tree/model
        with open("/proc/device-tree/model", "r") as file:
            model_name = file.read().strip()
        # Previous to Orin, this symbolic link points to the GPU load file
        gpu_load_path = "/sys/devices/gpu.0/load" 
        if "orin" in model_name.lower():
            # The location has been changed on the orins - /sys/devices/platform/bus@0/17000000.gpu/load
            # There's a symbolic link here:
            gpu_load_path = "/sys/devices/platform/gpu.0/load"
             
        return model_name, gpu_load_path
    except FileNotFoundError:
        return "Model file not found."
    except Exception as e:
        return f"An error occurred: {e}"

# Retrieve and print the GPU load path
MODEL_NAME, GPU_LOAD_PATH = get_gpu_load_path()
print(GPU_LOAD_PATH)
print(MODEL_NAME)

def get_gpu_load():
    with open(GPU_LOAD_PATH, 'r') as f:
        value = f.read()
    return int(float(value.strip()) / 10)


# Read the GPU usage and gather the rest of the system statistics
async def update_data():
    while True:
        latest_data["gpu_percent"] = get_gpu_load()
        # Tell the fans!
        for connection in list(active_connections):
            await connection.send_text(json.dumps(latest_data))
        # Sleep asynchronously for 1 second
        await asyncio.sleep(1)

app, rt = fast_app()

host_ip = "127.0.0.1"
port = "5000"

setup_script = f''' 
    <script>
        const hostIp = '{host_ip}';
        const port = '{port}';
    </script>
    <script src="../static/app_websocket_graph.js" defer></script>
'''

@rt('/')
def get():
    gpu_load = get_gpu_load()
    page = Html( Head(Title('Jetson Websocket Example'),
                NotStr(setup_script)),
                Link(rel="stylesheet",
             href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap"),
                Link(rel="stylesheet", href="../static/style_tutorial.css"), 
                Script(src="https://cdn.jsdelivr.net/npm/chart.js",
               type="text/javascript"),
    Body( Div( H2(MODEL_NAME), 
            # GPU Chart Container
            Div(
                Div(
                    H3("GPU"),
                    H2(
                        Span(" 0", id="usageNumberGpu", cls="usagePercentNumber"), Span(
                            "%", id="usagePercentSignGpu", cls="usagePercentSign"),
                        id="usagePercentageGpu"
                    ),
                    cls="chart-header"  
                ),
                Canvas(id="gpuChart", width="240", height="60"),
                cls="chart-container"  
            ),
            cls="chart-wrapper"),
        Div("Disconnected", id="connection-status", cls="connection-status"),

    ))
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