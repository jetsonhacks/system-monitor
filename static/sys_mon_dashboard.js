// Import Chart.js or include it via a script tag in your HTML
// <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

let lastData = {
    cpu_percent: 0,
    gpu_percent: 0,
    memory_percent: 0,
    memory_used: "0.00 GB",
    cached_files: "0.00 GB",
    swap_used: "0.00 MB",
    physical_memory: "4.00 GB"
};

const charts = {};

// Function to update the UI based on the latest data
function updateUI(data) {
    lastData = data;
    const currentTime = new Date().toLocaleTimeString();

    // Update the values on the front face
    const percentageElements = {
        gpu: document.getElementById('usagePercentageGpu'),
        cpu: document.getElementById('usagePercentageCpu'),
        memory: document.getElementById('usagePercentageMemory')
    };

    for (const key in percentageElements) {
        const value = Math.floor(lastData[`${key}_percent`]);
        percentageElements[key].innerHTML = `<span class="usagePercentNumber" id="usageNumber${key.charAt(0).toUpperCase() + key.slice(1)}">${value}</span><span class="usagePercentSign" id="usagePercentSign${key.charAt(0).toUpperCase() + key.slice(1)}">%</span>`;
    }

    // Update the back face memory details
    document.getElementById('physicalMemory').innerText = `${lastData.physical_memory}`;
    document.getElementById('memoryUsed').innerText = `${lastData.memory_used}`;
    document.getElementById('cachedFiles').innerText = `${lastData.cached_files}`;
    document.getElementById('swapUsed').innerText = `${lastData.swap_used}`;

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

document.addEventListener("DOMContentLoaded", function () {
    const chartConfigs = {
        cpu: {
            ctx: document.getElementById('cpuChart').getContext('2d'),
            label: 'CPU Usage (%)',
            type: 'line',
            maxPoints: 60,
            borderColor: 'rgba(135, 199, 247, 0.8)',
            borderWidth: 2,
            backgroundColor: 'rgba(135, 199, 247, 0.2)',
            pointRadius: 0,
            annotation: createAnnotation(75, 'High Usage')
        },
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
        memory: {
            ctx: document.getElementById('memoryChart').getContext('2d'),
            label: 'Memory Usage (%)',
            type: 'line',
            maxPoints: 60,
            borderColor: 'rgba(181, 135, 232, 0.8)',
            borderWidth: 2,
            backgroundColor: 'rgba(181, 135, 232, 0.2)',
            pointRadius: 0,
            annotation: createAnnotation(70, 'High Usage')
        }
    };

    for (const key in chartConfigs) {
        charts[key] = createChart(chartConfigs[key].ctx, chartConfigs[key]);
    }

    // Memory Container Flip Handling
    const memoryContainer = document.querySelector('.memory-container');
    const frontFace = memoryContainer.querySelector('.chart-front');
    const backFace = memoryContainer.querySelector('.chart-back');

    // Handle flipping logic
    const infoButton = frontFace.querySelector('.info-button');
    if (infoButton) {
        infoButton.onclick = function () {
            memoryContainer.classList.toggle('flipped');
        };
    }

    const backButton = backFace.querySelector('.info-back-button');
    if (backButton) {
        backButton.onclick = function () {
            memoryContainer.classList.toggle('flipped');
        };
    }

});