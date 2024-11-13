const statusElement = document.getElementById('connection-status');
const ws = new WebSocket(`ws://${hostIp}:${port}/update-data`);

function updateUI(data) {
    gpu_load.innerText = data.gpu_load
};

function updateStatus (text, color) {
    statusElement.innerText = text;
    statusElement.style.color = color;
    statusElement.style.display = "block";
};

ws.onmessage = (event) => {
    try {
        const newData = JSON.parse(event.data);
        updateUI(newData);
    } catch (error) {
        console.error("Failed to parse incoming data:", error);
    }
};

ws.onopen = () => {
    console.log("WebSocket connection established.");
    statusElement.style.display = "none";
};

ws.onclose = () => {
    console.log("WebSocket connection closed.");
    updateStatus("Disconnected", "lightslategrey");
};

ws.onerror = (event) => {
    console.error("WebSocket error:", event);
    updateStatus("Connection Error", "orange");
};

