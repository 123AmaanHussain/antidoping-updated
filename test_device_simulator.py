import asyncio
import random
import json
from datetime import datetime, timedelta

class MockBluetoothDevice:
    def __init__(self, name="Test Fitness Band", address="00:11:22:33:44:55", device_type="generic"):
        self.name = name
        self.address = address
        self.device_type = device_type
        self.heart_rate = 70
        self.steps = 0
        self.is_connected = False
        self.start_time = None
        self.battery_level = 100
        self.last_sync = datetime.now()

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
            'device_name': self.name,
            'device_type': self.device_type,
            'heart_rate': round(self.simulate_heart_rate()),
            'steps': self.simulate_steps(),
            'battery_level': self.battery_level,
            'last_sync': self.last_sync.isoformat(),
            'timestamp': datetime.now().isoformat(),
            'connection_status': 'Connected' if self.is_connected else 'Disconnected'
        }

class TestDeviceSimulator:
    def __init__(self):
        self.devices = [
            MockBluetoothDevice("Firebolt Fitness Tracker", "FB:12:34:56:78:90", "firebolt"),
            MockBluetoothDevice("Mi Band 6", "12:34:56:78:90:AB", "mi_band"),
            MockBluetoothDevice("Fitbit Charge 5", "AB:CD:EF:12:34:56", "fitbit"),
            MockBluetoothDevice("Apple Watch", "98:76:54:32:10:EF", "apple")
        ]
        self.connected_device = None
        self.scanning = False

    async def scan_devices(self):
        """Simulate device scanning."""
        if self.scanning:
            return {"status": "error", "message": "Scan already in progress"}
        
        try:
            self.scanning = True
            await asyncio.sleep(2)  # Simulate scanning delay
            
            # Add some randomization to make scanning more realistic
            available_devices = []
            for device in self.devices:
                if random.random() > 0.1:  # 90% chance device is discoverable
                    available_devices.append({
                        "name": device.name,
                        "address": device.address,
                        "type": device.device_type,
                        "rssi": random.randint(-90, -40),  # Simulate signal strength
                        "battery": device.battery_level
                    })
            
            return {"status": "success", "devices": available_devices}
        
        except Exception as e:
            return {"status": "error", "message": str(e)}
        finally:
            self.scanning = False

    async def connect_device(self, address):
        """Simulate connecting to a device."""
        try:
            # Find the device with matching address
            device = next((d for d in self.devices if d.address == address), None)
            
            if not device:
                return {"status": "error", "message": "Device not found"}

            await asyncio.sleep(1)  # Simulate connection delay
            
            # Simulate connection success rate
            if random.random() > 0.1:  # 90% success rate
                device.is_connected = True
                device.last_sync = datetime.now()
                self.connected_device = device
                
                return {
                    "status": "success",
                    "device": {
                        "name": device.name,
                        "address": device.address,
                        "type": device.device_type,
                        "battery": device.battery_level,
                        "last_sync": device.last_sync.isoformat()
                    }
                }
            else:
                return {"status": "error", "message": "Failed to connect. Please try again."}
                
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def get_monitoring_data(self, duration_seconds=60):
        """Get monitoring data from the connected device."""
        if not self.connected_device:
            return {"status": "error", "message": "No device connected"}
            
        try:
            data_points = []
            start_time = datetime.now()
            
            # Simulate collecting data points
            while (datetime.now() - start_time).seconds < duration_seconds:
                data_points.append(self.connected_device.get_data())
                await asyncio.sleep(1)  # Collect data every second
                
            return {
                "status": "success",
                "device_name": self.connected_device.name,
                "data": data_points
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def disconnect_device(self):
        """Disconnect from the current device."""
        if self.connected_device:
            await asyncio.sleep(0.5)  # Simulate disconnection delay
            self.connected_device.is_connected = False
            self.connected_device = None
            return {"status": "success", "message": "Device disconnected"}
        return {"status": "error", "message": "No device connected"}

# Global simulator instance
simulator = TestDeviceSimulator()
