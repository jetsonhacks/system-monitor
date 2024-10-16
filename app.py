from fasthtml.common import *
from starlette.websockets import WebSocket
import psutil
import asyncio
import json
import configparser

# Get the server configuration
config = configparser.ConfigParser()
try:
    config.read('server_config.ini')
    host_ip = config['server']['host']
    port = int(config['server']['port'])
except (KeyError, ValueError, configparser.Error):
    host_ip = 'localhost'
    port = 5000

# Global variable to store the latest GPU load data
latest_data = {
    "cpu_percent": 0,
    "gpu_percent": 0.0,
    "memory_percent": 0,
    "memory_used": "0.00 GB",
    "cached_files": "0.00 GB",
    "swap_used": "0.00 MB",
    "physical_memory": "0.00 GB"
}

class ConnectionManager:
    def __init__(self):
        self.active_connections = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in list(self.active_connections):
            await connection.send_text(message)

# Create an instance of ConnectionManager
connection_manager = ConnectionManager()

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

# Broadcast the system monitor data to attach clients over websockets
async def broadcast_update_data():
    # Websocket expects JSON
    await connection_manager.broadcast(json.dumps(latest_data))

# Read the GPU usage and gather the rest of the system statistics
async def update_data():
    while True:
        try:
            # Update CPU usage
            latest_data["cpu_percent"] = psutil.cpu_percent(interval=1)
            
            # Update memory usage
            memory_info = psutil.virtual_memory()
            latest_data["memory_percent"] = memory_info.percent
            latest_data["memory_used"] = f"{memory_info.used / (1024 ** 3):.2f} GB"
            latest_data["cached_files"] = f"{memory_info.cached / (1024 ** 3):.2f} GB"
            
            swap_used_value = psutil.swap_memory().used / (1024 ** 3)
            if swap_used_value < 1:
                latest_data["swap_used"] = f"{swap_used_value * 1024:.2f} MB"
            else:
                latest_data["swap_used"] = f"{swap_used_value:.2f} GB"
                
            latest_data["physical_memory"] = f"{math.ceil(memory_info.total / (1024 ** 3)):.2f} GB"

            # Update GPU usage
            with open(GPU_LOAD_PATH, 'r') as f:
                value = f.read()
                latest_data["gpu_percent"] = float(value.strip()) / 10

        except (FileNotFoundError, ValueError, OSError) as e:
            latest_data["gpu_percent"] = 0.0

        await broadcast_update_data()
        # Sleep asynchronously for 1 second
        await asyncio.sleep(1)

app, rt = fast_app(pico=False, htmx=False, htmlkw={'lang':'en-US'})

# This script is the websocket code for the client browser
# Double curly braces are used in the f-string to escape { } characters
# statusElement is the div which tells if the client is disconnected
data_update_websocket_script = f"""
<script>

    const statusElement = document.getElementById('connection-status');

    const ws = new WebSocket('ws://{host_ip}:{port}/update-data');
    
    ws.onmessage = function(event) {{
        const data = event.data;
        try {{
            // Parse the incoming data and update the UI
            const newData = JSON.parse(event.data);
            updateUI(newData);
        }} catch (error) {{
            console.error("Failed to parse incoming data:", error);
        }}
    }};

    ws.onopen = function(event) {{
        console.log("WebSocket connection established.");
        statusElement.style.display = "none";
    }};

    ws.onclose = function(event) {{
        console.log("WebSocket connection closed.");
        statusElement.innerText = "Disconnected";
        statusElement.style.color = "lightslategrey";
        statusElement.style.display = "block";
    }};

    ws.onerror = function(event) {{
        console.error("WebSocket error:", event);
        statusElement.innerText = "Connection Error";
        statusElement.style.color = "orange";
        statusElement.style.display = "block";
    }};
</script>
"""

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(update_data())

# This route returns just the raw system monitor data
@app.get("/sys-mon")
def get_system_activity():
    return latest_data

# This is the 'back' of the memory display card
def memory_chart_detailed():
    return Div(
        Button(
            ">",
            cls="info-back-button",
        ),
        Div(
            Div(
                Span("Physical Memory:",
                     cls="memory-info-label"),
                # Static information
                Span("4.00 GB", id="physicalMemory",
                     cls="memory-info-value"),
                cls="memory-info"
            ),
            Div(
                Span("Memory Used:", cls="memory-info-label"),
                # Updated dynamically
                Span("0.00 GB", id="memoryUsed",
                     cls="memory-info-value"),
                cls="memory-info"
            ),
            Div(
                Span("Cached Files:", cls="memory-info-label"),
                # Updated dynamically
                Span("0.00 GB", id="cachedFiles",
                     cls="memory-info-value"),
                cls="memory-info"
            ),
            Div(
                Span("Swap Used:", cls="memory-info-label"),
                # Updated dynamically
                Span("0.00 MB", id="swapUsed",
                     cls="memory-info-value"),
                cls="memory-info"
            ),
            cls="usage-wrapper"
        ),
        cls="chart-back"
    )

# Main page
@rt('/')
def get():
    page = Title('Jetson Resource Monitor'), Body(
        # Roboto font
        Link(rel="stylesheet",
             href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap"),
        Link(rel="stylesheet", href="/static/style.css"),
        H3(MODEL_NAME, cls="model-title"),          
        Div(
            # CPU Chart Container
            Div(
                Div(
                    H3("CPU"),
                    H2(
                        Span(" 0", id="usageNumberCpu", cls="usagePercentNumber"), Span(
                            "%", id="usagePercentSignCpu", cls="usagePercentSign"),
                        id="usagePercentageCpu"
                    ),
                    cls="chart-header"  
                ),
                Canvas(id="cpuChart", width="240", height="60"),
                cls="chart-container"  
            ),
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
            Div(
                # Memory Chart Container
                Div(
                    # Front Face Div
                    Div(
                        H3("MEM"),
                        Div(
                            H2(
                                Span(" 0", id="usageNumberMemory", cls="usagePercentNumber"), Span(
                                    "%", id="usagePercentSignMemory", cls="usagePercentSign"),
                                id="usagePercentageMemory"
                            ),
                            Button(
                                NotStr(
                                    """<svg focusable="false" width="20" height="20" viewBox="0 0 24 24">
                                            <path d="M11 7h2v2h-2zm0 4h2v6h-2z"></path>
                                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"></path>
                                        </svg>"""
                                ),
                                cls="info-button"
                            ),
                            # Position relative to position button in top-right corner
                            style="position: relative;",
                            cls="usage-wrapper"
                        ),
                        cls="chart-header"
                    ),
                    Canvas(id="memoryChart", width="240", height="60"),
                    cls="chart-front"
                ),
                # Back Face Div
                memory_chart_detailed(),

                cls="chart-container memory-container",
                style="position: relative; width: 240px; height: 140px;"
            ),
            cls = "dashboard-container"
        ),
        Div("Disconnected", id="connection-status", cls="connection-status"),
        Script(src="/static/sys_mon_dashboard.js", type="text/javascript"),
        NotStr(data_update_websocket_script),
        Script(src="https://cdn.jsdelivr.net/npm/chart.js",
               type="text/javascript")
    )
    return page

# Websocket enpoint of update-data
async def websocket_endpoint(websocket: WebSocket):
    await connection_manager.connect(websocket)
    print("New client connected.")
    try:
        # The endpoint now just waits for the client to send messages
        while True:
            data = await websocket.receive_text()
            print(f"Message from client: {data}")
            # await websocket.send_text(f"Server echo: {data}")
    except Exception as e:
        print(f"WebSocket connection closed: {e}")
    finally:
        connection_manager.disconnect(websocket)
        print("Client disconnected.")

app.routes.append(WebSocketRoute('/update-data', websocket_endpoint))

if __name__ == "__main__":
    serve(host='0.0.0.0',port=port)

