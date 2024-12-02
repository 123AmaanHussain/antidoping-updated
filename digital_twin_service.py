import asyncio
import logging
from datetime import datetime
from test_device_simulator import simulator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DigitalTwin:
    def __init__(self):
        self.simulator = simulator
        self.alerts = []
    
    async def initialize(self, device_address=None):
        """Initialize the digital twin with a device."""
        if device_address:
            connected = await self.simulator.connect_device(device_address)
            if not connected:
                raise Exception("Failed to connect to device")
    
    async def scan_devices(self):
        """Scan for available BLE devices."""
        try:
            devices = await self.simulator.scan_devices()
            logger.info(f"Found {len(devices)} devices")
            return devices
        except Exception as e:
            logger.error(f"Failed to scan devices: {str(e)}")
            return []
    
    async def connect_device(self, address):
        """Connect to a specific device by address."""
        try:
            connected = await self.simulator.connect_device(address)
            if connected:
                logger.info(f"Connected to device: {address}")
            return connected
        except Exception as e:
            logger.error(f"Failed to connect: {str(e)}")
            return False
    
    async def get_monitoring_data(self, duration_seconds=60):
        """Get monitoring data from the device."""
        try:
            data = await self.simulator.get_monitoring_data(duration_seconds)
            return data
        except Exception as e:
            logger.error(f"Error getting monitoring data: {str(e)}")
            return None

# Example usage function
async def monitor_athlete(duration_seconds=60):
    """Monitor an athlete for a specified duration."""
    digital_twin = DigitalTwin()
    
    try:
        # Get monitoring data
        data = await digital_twin.get_monitoring_data(duration_seconds)
        
        if data:
            return data
        return None
        
    except Exception as e:
        logger.error(f"Error during monitoring: {str(e)}")
        return None
