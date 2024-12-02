// Digital Twin Management
class DigitalTwinManager {
    constructor() {
        this.heartRateChart = null;
        this.stepsChart = null;
        this.isMonitoring = false;
        this.deviceAddress = null;
        this.scanTimeout = null;
        this.initializeCharts();
        this.bindEvents();
    }

    initializeCharts() {
        const chartOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    font: {
                        size: 16
                    }
                }
            },
            animation: {
                duration: 750,
                easing: 'easeInOutQuart'
            }
        };

        // Initialize Heart Rate Chart
        const heartRateCtx = document.getElementById('heartRateChart').getContext('2d');
        this.heartRateChart = new Chart(heartRateCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Heart Rate (BPM)',
                    data: [],
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                ...chartOptions,
                plugins: {
                    ...chartOptions.plugins,
                    title: {
                        ...chartOptions.plugins.title,
                        text: 'Real-time Heart Rate'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        suggestedMax: 200,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    }
                }
            }
        });

        // Initialize Steps Chart
        const stepsCtx = document.getElementById('stepsChart').getContext('2d');
        this.stepsChart = new Chart(stepsCtx, {
            type: 'bar',
            data: {
                labels: ['Steps'],
                datasets: [{
                    label: 'Total Steps',
                    data: [0],
                    backgroundColor: 'rgb(75, 192, 192)',
                    borderColor: 'rgb(75, 192, 192)',
                    borderWidth: 1
                }]
            },
            options: {
                ...chartOptions,
                plugins: {
                    ...chartOptions.plugins,
                    title: {
                        ...chartOptions.plugins.title,
                        text: 'Step Count'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    }
                }
            }
        });
    }

    bindEvents() {
        document.getElementById('scanDevices').addEventListener('click', () => this.scanDevices());
        document.getElementById('startMonitoring').addEventListener('click', () => this.toggleMonitoring());
    }

    async scanDevices() {
        const scanButton = document.getElementById('scanDevices');
        const deviceList = document.getElementById('deviceList');
        
        try {
            // Disable scan button and show loading state
            scanButton.disabled = true;
            scanButton.innerHTML = `
                <div class="loading-spinner"></div>
                Scanning...
            `;
            
            deviceList.innerHTML = `
                <div class="text-center p-4">
                    <div class="loading-spinner"></div>
                    <p class="mt-2">Searching for nearby devices...</p>
                </div>
            `;
            
            const response = await fetch('/api/digital-twin/scan');
            const data = await response.json();
            
            if (data.status === 'success' && data.devices.length > 0) {
                deviceList.innerHTML = '';
                data.devices.forEach(device => {
                    const deviceElement = document.createElement('div');
                    deviceElement.className = 'device-item';
                    deviceElement.innerHTML = `
                        <div class="device-info">
                            <i class="fas fa-bluetooth device-icon"></i>
                            <div>
                                <div class="device-name">${device.name || 'Unknown Device'}</div>
                                <div class="device-status">${device.address}</div>
                            </div>
                        </div>
                        <button onclick="digitalTwin.connectDevice('${device.address}')" class="connect-btn">
                            <i class="fas fa-link"></i> Connect
                        </button>
                    `;
                    deviceList.appendChild(deviceElement);
                });
            } else {
                deviceList.innerHTML = `
                    <div class="text-center p-4">
                        <i class="fas fa-exclamation-circle fa-2x text-warning"></i>
                        <p class="mt-2">No devices found. Make sure your device is nearby and Bluetooth is enabled.</p>
                        <button onclick="digitalTwin.scanDevices()" class="btn btn-primary mt-3">
                            <i class="fas fa-sync"></i> Try Again
                        </button>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error scanning devices:', error);
            deviceList.innerHTML = `
                <div class="text-center p-4">
                    <i class="fas fa-exclamation-triangle fa-2x text-danger"></i>
                    <p class="mt-2">Error scanning for devices. Please try again.</p>
                    <button onclick="digitalTwin.scanDevices()" class="btn btn-primary mt-3">
                        <i class="fas fa-sync"></i> Try Again
                    </button>
                </div>
            `;
            showAlert('Error scanning for devices', 'error');
        } finally {
            // Reset scan button
            scanButton.disabled = false;
            scanButton.innerHTML = `<i class="fas fa-search"></i> Scan for Devices`;
        }
    }

    async connectDevice(address) {
        const connectBtn = event.target.closest('.connect-btn');
        const originalContent = connectBtn.innerHTML;
        
        try {
            connectBtn.disabled = true;
            connectBtn.innerHTML = `
                <div class="loading-spinner"></div>
                Connecting...
            `;
            
            const response = await fetch('/api/digital-twin/connect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ device_address: address })
            });
            const data = await response.json();
            
            if (data.status === 'success') {
                this.deviceAddress = address;
                connectBtn.innerHTML = `<i class="fas fa-check"></i> Connected`;
                connectBtn.classList.add('btn-success');
                document.getElementById('startMonitoring').disabled = false;
                showAlert('Connected to device successfully', 'success');
                
                // Update other connect buttons
                document.querySelectorAll('.connect-btn').forEach(btn => {
                    if (btn !== connectBtn) {
                        btn.disabled = true;
                    }
                });
            } else {
                throw new Error(data.message);
            }
        } catch (error) {
            console.error('Error connecting to device:', error);
            connectBtn.innerHTML = originalContent;
            connectBtn.disabled = false;
            showAlert('Error connecting to device', 'error');
        }
    }

    async toggleMonitoring() {
        const monitorBtn = document.getElementById('startMonitoring');
        
        if (!this.isMonitoring) {
            try {
                this.isMonitoring = true;
                monitorBtn.innerHTML = `
                    <div class="loading-spinner"></div>
                    Monitoring...
                `;
                
                const response = await fetch('/api/digital-twin/monitor', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ duration: 3600 }) // 1 hour monitoring
                });
                
                const data = await response.json();
                if (data.status === 'success') {
                    this.updateCharts(data.data);
                    this.updateStats(data.data.statistics);
                    this.checkAlerts(data.data.alerts);
                    monitorBtn.innerHTML = `<i class="fas fa-stop"></i> Stop Monitoring`;
                    monitorBtn.classList.remove('btn-success');
                    monitorBtn.classList.add('btn-danger');
                }
            } catch (error) {
                console.error('Error during monitoring:', error);
                showAlert('Error during monitoring', 'error');
                this.isMonitoring = false;
                monitorBtn.innerHTML = `<i class="fas fa-play"></i> Start Monitoring`;
                monitorBtn.classList.remove('btn-danger');
                monitorBtn.classList.add('btn-success');
            }
        } else {
            this.isMonitoring = false;
            monitorBtn.innerHTML = `<i class="fas fa-play"></i> Start Monitoring`;
            monitorBtn.classList.remove('btn-danger');
            monitorBtn.classList.add('btn-success');
        }
    }

    updateCharts(data) {
        if (data.raw_data && data.raw_data.length > 0) {
            const timestamps = data.raw_data.map(d => new Date(d.timestamp).toLocaleTimeString());
            const heartRates = data.raw_data.map(d => d.heart_rate);
            
            this.heartRateChart.data.labels = timestamps;
            this.heartRateChart.data.datasets[0].data = heartRates;
            this.heartRateChart.update('none'); // Disable animation for performance

            const latestSteps = data.statistics.total_steps || 0;
            this.stepsChart.data.datasets[0].data = [latestSteps];
            this.stepsChart.update('none');
        }
    }

    updateStats(statistics) {
        if (statistics) {
            document.getElementById('avgHeartRate').textContent = 
                Math.round(statistics.avg_heart_rate) || '--';
            document.getElementById('maxHeartRate').textContent = 
                Math.round(statistics.max_heart_rate) || '--';
            document.getElementById('totalSteps').textContent = 
                statistics.total_steps?.toLocaleString() || '--';
            document.getElementById('activityDuration').textContent = 
                Math.round(statistics.activity_duration) || '--';
        }
    }

    checkAlerts(alerts) {
        if (alerts && alerts.length > 0) {
            alerts.forEach(alert => {
                let icon = 'info-circle';
                if (alert.type === 'anomaly') icon = 'exclamation-triangle';
                
                showAlert(`
                    <i class="fas fa-${icon}"></i>
                    ${alert.message}
                `, 'warning');
            });
        }
    }
}

// Initialize Digital Twin Manager
let digitalTwin;
document.addEventListener('DOMContentLoaded', () => {
    digitalTwin = new DigitalTwinManager();
});

// Utility function to show alerts
function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.innerHTML = message;
    
    const alertsContainer = document.getElementById('alerts');
    alertsContainer.appendChild(alertDiv);
    
    // Add slide-out animation before removing
    setTimeout(() => {
        alertDiv.style.transform = 'translateX(100%)';
        alertDiv.style.opacity = '0';
        setTimeout(() => alertDiv.remove(), 300);
    }, 4700);
}
