import asyncio
import random
import json
from datetime import datetime, timedelta

class MockBluetoothDevice:
    def __init__(self, name="Test Fitness Band", address="00:11:22:33:44:55"):
        self.name = name
        self.address = address
        self.heart_rate = 70
        self.steps = 0
        self.is_connected = False
        self.start_time = None

    def simulate_heart_rate(self):
        """Simulate realistic heart rate changes."""
        variation = random.uniform(-5, 5)
        self.heart_rate = max(60, min(180, self.heart_rate + variation))
        return self.heart_rate

    def simulate_steps(self):
        """Simulate step count increases."""
        new_steps = random.randint(10, 30)
        self.steps += new_steps
        return self.steps

    def get_data(self):
        """Get current device data."""
        return {
            'heart_rate': round(self.simulate_heart_rate()),
            'steps': self.simulate_steps(),
            'timestamp': datetime.now().isoformat()
        }

class TestDeviceSimulator:
    def __init__(self):
        self.devices = [
            MockBluetoothDevice("Mi Band 6", "12:34:56:78:90:AB"),
            MockBluetoothDevice("Fitbit Charge 5", "AB:CD:EF:12:34:56"),
            MockBluetoothDevice("Apple Watch", "98:76:54:32:10:EF")
        ]
        self.connected_device = None

    async def scan_devices(self):
        """Simulate device scanning."""
        await asyncio.sleep(2)  # Simulate scanning delay
        return [{"name": d.name, "address": d.address} for d in self.devices]

    async def connect_device(self, address):
        """Simulate connecting to a device."""
        await asyncio.sleep(1)  # Simulate connection delay
        
        device = next((d for d in self.devices if d.address == address), None)
        if device:
            device.is_connected = True
            device.start_time = datetime.now()
            self.connected_device = device
            return True
        return False

    async def get_monitoring_data(self, duration_seconds=60):
        """Simulate monitoring data collection."""
        if not self.connected_device:
            return None

        data_points = []
        current_time = self.connected_device.start_time or datetime.now()
        
        # Generate data points
        for i in range(duration_seconds):
            data_point = self.connected_device.get_data()
            data_points.append(data_point)
            current_time += timedelta(seconds=1)
            await asyncio.sleep(0.1)  # Simulate data collection delay

        # Calculate statistics
        heart_rates = [d['heart_rate'] for d in data_points]
        steps = max([d['steps'] for d in data_points])
        
        return {
            'status': 'success',
            'data': {
                'raw_data': data_points,
                'statistics': {
                    'avg_heart_rate': sum(heart_rates) / len(heart_rates),
                    'max_heart_rate': max(heart_rates),
                    'total_steps': steps,
                    'activity_duration': duration_seconds / 60  # in minutes
                },
                'alerts': self._generate_alerts(heart_rates)
            }
        }

    def _generate_alerts(self, heart_rates):
        """Generate alerts based on heart rate data."""
        alerts = []
        avg_hr = sum(heart_rates) / len(heart_rates)
        hr_std = (sum((x - avg_hr) ** 2 for x in heart_rates) / len(heart_rates)) ** 0.5

        for hr in heart_rates:
            if abs(hr - avg_hr) > 2 * hr_std:
                alerts.append({
                    'type': 'anomaly',
                    'message': f'Unusual heart rate detected: {hr} BPM',
                    'value': hr,
                    'timestamp': datetime.now().isoformat()
                })

        return alerts

# Global simulator instance
simulator = TestDeviceSimulator()
