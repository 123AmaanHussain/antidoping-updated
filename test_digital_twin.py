import asyncio
from digital_twin_service import DigitalTwin
import json

async def test_digital_twin():
    print("\n=== Testing Digital Twin Feature ===\n")
    
    # Create Digital Twin instance
    dt = DigitalTwin()
    
    # 1. Test device scanning
    print("1. Scanning for devices...")
    devices = await dt.scan_devices()
    print(f"Found {len(devices)} devices:")
    for device in devices:
        print(f"  - {device['name']} ({device['address']})")
    
    if devices:
        # 2. Test device connection
        test_device = devices[0]
        print(f"\n2. Connecting to {test_device['name']}...")
        connected = await dt.connect_device(test_device['address'])
        print(f"Connection {'successful' if connected else 'failed'}")
        
        if connected:
            # 3. Test monitoring
            print("\n3. Starting monitoring (10 seconds)...")
            data = await dt.get_monitoring_data(10)
            
            if data:
                print("\nMonitoring Results:")
                stats = data['data']['statistics']
                print(f"  Average Heart Rate: {stats['avg_heart_rate']:.1f} BPM")
                print(f"  Maximum Heart Rate: {stats['max_heart_rate']} BPM")
                print(f"  Total Steps: {stats['total_steps']}")
                print(f"  Activity Duration: {stats['activity_duration']} minutes")
                
                if data['data']['alerts']:
                    print("\nAlerts:")
                    for alert in data['data']['alerts']:
                        print(f"  - {alert['message']}")
            else:
                print("No monitoring data received")

if __name__ == "__main__":
    asyncio.run(test_digital_twin())
