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
        self.connected_device = None
        self.last_scan_result = None
    
    async def initialize(self, device_address=None):
        """Initialize the digital twin with a device."""
        try:
            if device_address:
                result = await self.simulator.connect_device(device_address)
                if result["status"] == "success":
                    self.connected_device = result["device"]
                    logger.info(f"Successfully initialized with device: {self.connected_device['name']}")
                    return {"status": "success", "device": self.connected_device}
                else:
                    logger.error(f"Failed to initialize device: {result['message']}")
                    return result
            return {"status": "success", "message": "Digital Twin initialized without device"}
        except Exception as e:
            logger.error(f"Initialization error: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def scan_devices(self):
        """Scan for available BLE devices."""
        try:
            logger.info("Starting device scan...")
            result = await self.simulator.scan_devices()
            
            if result["status"] == "success":
                self.last_scan_result = result["devices"]
                logger.info(f"Found {len(self.last_scan_result)} devices")
                
                # Log found devices
                for device in self.last_scan_result:
                    logger.info(f"Found device: {device['name']} ({device['address']})")
                
                return {
                    "status": "success",
                    "devices": self.last_scan_result,
                    "message": f"Found {len(self.last_scan_result)} devices"
                }
            else:
                logger.error(f"Scan failed: {result['message']}")
                return result
                
        except Exception as e:
            logger.error(f"Failed to scan devices: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def connect_device(self, address):
        """Connect to a specific device by address."""
        try:
            logger.info(f"Attempting to connect to device: {address}")
            result = await self.simulator.connect_device(address)
            
            if result["status"] == "success":
                self.connected_device = result["device"]
                logger.info(f"Successfully connected to {self.connected_device['name']}")
                return result
            else:
                logger.error(f"Connection failed: {result['message']}")
                return result
                
        except Exception as e:
            logger.error(f"Failed to connect: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def get_monitoring_data(self, duration_seconds=60):
        """Get monitoring data from the device."""
        try:
            if not self.connected_device:
                return {"status": "error", "message": "No device connected"}
                
            logger.info(f"Getting monitoring data for {duration_seconds} seconds")
            result = await self.simulator.get_monitoring_data(duration_seconds)
            
            if result["status"] == "success":
                # Process and analyze the data
                data_points = result["data"]
                
                # Calculate statistics
                heart_rates = [point['heart_rate'] for point in data_points]
                steps = max([point['steps'] for point in data_points])
                
                stats = {
                    'avg_heart_rate': sum(heart_rates) / len(heart_rates),
                    'max_heart_rate': max(heart_rates),
                    'min_heart_rate': min(heart_rates),
                    'total_steps': steps,
                    'duration': duration_seconds,
                    'device_name': self.connected_device['name'],
                    'device_type': self.connected_device['type'],
                    'battery_level': self.connected_device['battery'],
                    'last_sync': self.connected_device['last_sync']
                }
                
                return {
                    "status": "success",
                    "data": data_points,
                    "statistics": stats
                }
            else:
                logger.error(f"Failed to get monitoring data: {result['message']}")
                return result
                
        except Exception as e:
            logger.error(f"Error getting monitoring data: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def disconnect_current_device(self):
        """Disconnect from the current device."""
        try:
            if self.connected_device:
                result = await self.simulator.disconnect_device()
                if result["status"] == "success":
                    self.connected_device = None
                return result
            return {"status": "error", "message": "No device connected"}
        except Exception as e:
            logger.error(f"Error disconnecting device: {str(e)}")
            return {"status": "error", "message": str(e)}

# Create a global instance
digital_twin = DigitalTwin()

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
