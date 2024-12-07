// Digital Twin Management
class DigitalTwinManager {
    constructor() {
        this.heartRateChart = null;
        this.stepsChart = null;
        this.isMonitoring = false;
        this.deviceAddress = null;
        this.scanTimeout = null;
        this.monitoringInterval = null;
        this.connectedDevice = null;
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
            
            const response = await fetch('/digital-twin', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    action: 'scan'
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Scan response:', data); // Debug log
            
            if (data.status === 'success' && data.devices && data.devices.length > 0) {
                deviceList.innerHTML = '';
                data.devices.forEach(device => {
                    const deviceElement = document.createElement('div');
                    deviceElement.className = 'device-item';
                    
                    // Determine device icon and type-specific styling
                    let deviceIcon = 'bluetooth';
                    let deviceTypeClass = '';
                    if (device.type === 'firebolt') {
                        deviceIcon = 'bolt';
                        deviceTypeClass = 'text-warning';
                    }
                    
                    deviceElement.innerHTML = `
                        <div class="device-info">
                            <i class="fas fa-${deviceIcon} device-icon ${deviceTypeClass}"></i>
                            <div>
                                <div class="device-name">${device.name || 'Unknown Device'}</div>
                                <div class="device-status">
                                    Signal: ${this.getSignalStrengthLabel(device.rssi)}
                                    ${device.battery ? ` | Battery: ${device.battery}%` : ''}
                                </div>
                            </div>
                        </div>
                        <button class="connect-btn btn btn-primary">
                            <i class="fas fa-link"></i> Connect
                        </button>
                    `;
                    
                    // Add click event listener to connect button
                    const connectBtn = deviceElement.querySelector('.connect-btn');
                    connectBtn.addEventListener('click', () => this.connectDevice(device.address));
                    
                    deviceList.appendChild(deviceElement);
                });
                
                showAlert('Devices found successfully', 'success');
            } else {
                deviceList.innerHTML = `
                    <div class="text-center p-4">
                        <i class="fas fa-exclamation-circle fa-2x text-warning"></i>
                        <p class="mt-2">No devices found. Please ensure your device is:</p>
                        <ul class="list-unstyled">
                            <li><i class="fas fa-check-circle text-success"></i> Turned on</li>
                            <li><i class="fas fa-check-circle text-success"></i> In pairing mode</li>
                            <li><i class="fas fa-check-circle text-success"></i> Within range</li>
                        </ul>
                        <button onclick="digitalTwin.scanDevices()" class="btn btn-primary mt-3">
                            <i class="fas fa-sync"></i> Try Again
                        </button>
                    </div>
                `;
                showAlert('No devices found', 'warning');
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
            showAlert('Error scanning for devices: ' + error.message, 'error');
        } finally {
            // Reset scan button
            scanButton.disabled = false;
            scanButton.innerHTML = `<i class="fas fa-search"></i> Scan for Devices`;
        }
    }

    getSignalStrengthLabel(rssi) {
        if (!rssi) return 'Unknown';
        if (rssi >= -50) return 'Excellent';
        if (rssi >= -60) return 'Good';
        if (rssi >= -70) return 'Fair';
        return 'Poor';
    }

    async connectDevice(address) {
        if (!address) {
            showAlert('Invalid device address', 'error');
            return;
        }

        const connectBtn = event.target.closest('.connect-btn');
        const originalContent = connectBtn.innerHTML;
        
        try {
            connectBtn.disabled = true;
            connectBtn.innerHTML = `
                <div class="loading-spinner"></div>
                Connecting...
            `;
            
            const response = await fetch('/digital-twin', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    action: 'connect',
                    device_address: address
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Connect response:', data); // Debug log
            
            if (data.status === 'success') {
                this.connectedDevice = data.device;
                this.deviceAddress = address;
                
                // Update UI to show connected state
                document.getElementById('startMonitoring').disabled = false;
                connectBtn.innerHTML = `<i class="fas fa-check"></i> Connected`;
                connectBtn.classList.remove('btn-primary');
                connectBtn.classList.add('btn-success');
                
                // Disable other connect buttons
                document.querySelectorAll('.connect-btn').forEach(btn => {
                    if (btn !== connectBtn) {
                        btn.disabled = true;
                        btn.classList.add('btn-secondary');
                    }
                });
                
                showAlert(`Connected to ${data.device.name}`, 'success');
                
                // Start monitoring automatically
                await this.startMonitoring();
            } else {
                throw new Error(data.message || 'Failed to connect');
            }
        } catch (error) {
            console.error('Error connecting to device:', error);
            connectBtn.innerHTML = originalContent;
            connectBtn.disabled = false;
            showAlert(error.message || 'Failed to connect to device', 'error');
        }
    }

    async startMonitoring() {
        if (!this.deviceAddress) {
            showAlert('No device connected', 'error');
            return;
        }

        try {
            this.isMonitoring = true;
            document.getElementById('startMonitoring').innerHTML = `
                <i class="fas fa-stop"></i> Stop Monitoring
            `;

            // Start periodic data collection
            this.monitoringInterval = setInterval(async () => {
                try {
                    const response = await fetch('/digital-twin', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                        },
                        body: new URLSearchParams({
                            'action': 'get_data',
                            'duration': '60'
                        })
                    });

                    const data = await response.json();
                    
                    if (data.status === 'success') {
                        this.updateCharts(data);
                        this.updateStats(data.statistics);
                    } else {
                        throw new Error(data.message);
                    }
                } catch (error) {
                    console.error('Error getting monitoring data:', error);
                    this.stopMonitoring();
                    showAlert('Error getting monitoring data', 'error');
                }
            }, 1000);

        } catch (error) {
            console.error('Error starting monitoring:', error);
            this.stopMonitoring();
            showAlert('Error starting monitoring', 'error');
        }
    }

    stopMonitoring() {
        this.isMonitoring = false;
        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
            this.monitoringInterval = null;
        }
        document.getElementById('startMonitoring').innerHTML = `
            <i class="fas fa-play"></i> Start Monitoring
        `;
    }

    async toggleMonitoring() {
        if (this.isMonitoring) {
            this.stopMonitoring();
        } else {
            await this.startMonitoring();
        }
    }

    updateCharts(data) {
        if (!data.data || !Array.isArray(data.data)) return;

        const timestamps = data.data.map(d => new Date(d.timestamp).toLocaleTimeString());
        const heartRates = data.data.map(d => d.heart_rate);
        const steps = data.data[data.data.length - 1].steps;

        // Update heart rate chart
        this.heartRateChart.data.labels = timestamps;
        this.heartRateChart.data.datasets[0].data = heartRates;
        this.heartRateChart.update();

        // Update steps chart
        this.stepsChart.data.datasets[0].data = [steps];
        this.stepsChart.update();
    }

    updateStats(stats) {
        if (!stats) return;

        document.getElementById('avgHeartRate').textContent = Math.round(stats.avg_heart_rate);
        document.getElementById('maxHeartRate').textContent = Math.round(stats.max_heart_rate);
        document.getElementById('totalSteps').textContent = stats.total_steps;
        document.getElementById('activityDuration').textContent = Math.round(stats.duration / 60);
    }
}

// Initialize Digital Twin Manager
let digitalTwin;
document.addEventListener('DOMContentLoaded', () => {
    digitalTwin = new DigitalTwinManager();
});

// Utility function to show alerts
function showAlert(message, type = 'info') {
    const alertsContainer = document.getElementById('alerts');
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    
    let icon = 'info-circle';
    if (type === 'success') icon = 'check-circle';
    if (type === 'error') icon = 'exclamation-circle';
    if (type === 'warning') icon = 'exclamation-triangle';
    
    alert.innerHTML = `
        <i class="fas fa-${icon}"></i>
        <span>${message}</span>
    `;
    
    alertsContainer.appendChild(alert);
    
    // Remove alert after 5 seconds
    setTimeout(() => {
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 300);
    }, 5000);
}
