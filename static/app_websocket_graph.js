const statusElement = document.getElementById('connection-status');
const ws = new WebSocket(`ws://${hostIp}:${port}/update-data`);

/* Graph */
const charts = {};

let lastData = {
    gpu_percent: 0,
};

// Function to update the UI based on the latest data
function updateUI(data) {
    lastData = data;
    const currentTime = new Date().toLocaleTimeString();

    // Update the values on the front face
    const percentageElements = {
        gpu: document.getElementById('usagePercentageGpu'),
    };

    for (const key in percentageElements) {
        const value = Math.floor(lastData[`${key}_percent`]);
        percentageElements[key].innerHTML = `<span class="usagePercentNumber" id="usageNumber${key.charAt(0).toUpperCase() + key.slice(1)}">${value}</span><span class="usagePercentSign" id="usagePercentSign${key.charAt(0).toUpperCase() + key.slice(1)}">%</span>`;
    }

    // Update the charts
    for (const key in charts) {
        const chart = charts[key];
        chart.data.labels.push(currentTime);
        chart.data.datasets[0].data.push(lastData[`${key}_percent`]);
        if (chart.data.labels.length > 60) {
            chart.data.labels.shift();
            chart.data.datasets[0].data.shift();
        }
        chart.update();
    }
}

// Generalized function to create a chart with given configurations
function createChart(ctx, config) {
    return new Chart(ctx, {
        type: config.type,
        data: {
            labels: Array(config.maxPoints).fill(''),
            datasets: [{
                label: config.label,
                data: Array(config.maxPoints).fill(0),
                borderColor: config.borderColor,
                borderWidth: config.borderWidth,
                fill: true,
                backgroundColor: config.backgroundColor,
                pointRadius: config.pointRadius
            }]
        },
        options: {
            responsive: false,
            maintainAspectRatio: false,
            animation: {
                duration: 500,
                easing: 'linear'
            },
            scales: {
                x: {
                    display: false
                },
                y: {
                    min: 0,
                    max: 100,
                    display: true,
                    ticks: {
                        stepSize: 25,
                        display: false
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                annotation: config.annotation,
                title: {
                    display: false
                }
            }
        }
    });
}

// Generalized chart configuration function for annotations
function createAnnotation(yValue, label) {
    return {
        annotations: {
            threshold: {
                type: 'line',
                yMin: yValue,
                yMax: yValue,
                borderColor: 'rgba(255, 0, 0, 0.5)',
                borderWidth: 2,
                label: {
                    content: label,
                    enabled: true,
                    position: 'end'
                }
            }
        }
    };
}

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

document.addEventListener("DOMContentLoaded", function () {
    const chartConfigs = {
        gpu: {
            ctx: document.getElementById('gpuChart').getContext('2d'),
            label: 'GPU Usage (%)',
            type: 'line',
            maxPoints: 60,
            borderColor: 'rgba(135, 192, 143, 0.8)',
            borderWidth: 2,
            backgroundColor: 'rgba(135, 192, 143, 0.2)',
            pointRadius: 0,
            annotation: createAnnotation(80, 'High Usage')
        },
    };

    for (const key in chartConfigs) {
        charts[key] = createChart(chartConfigs[key].ctx, chartConfigs[key]);
    }

});
