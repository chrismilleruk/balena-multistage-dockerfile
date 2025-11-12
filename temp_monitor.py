#!/usr/bin/env python3
"""
Temperature Monitor for R4DCB08 8-Bit RS485 Temperature Receiver
Reads up to 8 DS18B20 sensors via MODBUS RTU protocol
"""

import time
import sys
import os
from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException

# Configuration from environment variables with defaults
SERIAL_PORT = os.getenv('SERIAL_PORT', '/dev/ttyACM0')
BAUDRATE = int(os.getenv('BAUDRATE', '9600'))
MODBUS_ADDRESS = int(os.getenv('MODBUS_ADDRESS', '1'))
TIMEOUT = int(os.getenv('TIMEOUT', '3'))
PARITY = os.getenv('PARITY', 'N')
STOPBITS = int(os.getenv('STOPBITS', '1'))
BYTESIZE = int(os.getenv('BYTESIZE', '8'))

# Temperature register addresses (function 03 - Read Holding Registers)
TEMP_START_REGISTER = int(os.getenv('TEMP_START_REGISTER', '0'))
NUM_SENSORS = int(os.getenv('NUM_SENSORS', '8'))
POLL_INTERVAL = int(os.getenv('POLL_INTERVAL', '5'))

def init_modbus_client():
    """Initialize MODBUS RTU client"""
    client = ModbusSerialClient(
        port=SERIAL_PORT,
        baudrate=BAUDRATE,
        parity=PARITY,
        stopbits=STOPBITS,
        bytesize=BYTESIZE,
        timeout=TIMEOUT
    )
    return client

def read_temperature_sensors(client, num_sensors=8):
    """
    Read temperature from all sensors using MODBUS function 03
    
    Args:
        client: ModbusSerialClient instance
        num_sensors: Number of sensors to read (default 8)
    
    Returns:
        dict: Sensor readings with sensor number as key
    """
    temperatures = {}
    
    try:
        # Read all 8 temperature registers at once
        # Most MODBUS temp receivers store one temperature per register
        result = client.read_holding_registers(
            address=TEMP_START_REGISTER,
            count=num_sensors,
            unit=MODBUS_ADDRESS
        )
        
        if result.isError():
            print(f"ERROR: MODBUS read failed: {result}")
            return temperatures
        
        # Process each sensor reading
        for i in range(num_sensors):
            raw_value = result.registers[i]
            
            # Convert raw value to temperature
            # R4DCB08 typically returns temperature in 0.1°C units or direct celsius
            # Check your device documentation for exact conversion
            # Common formats:
            # - Direct celsius (e.g., 25 = 25°C)
            # - 0.1°C units (e.g., 250 = 25.0°C)
            # - Signed 16-bit for negative temps
            
            # Handle signed temperatures (for negative values)
            if raw_value > 32767:  # If MSB is set (negative temperature)
                temperature = (raw_value - 65536) / 10.0
            else:
                temperature = raw_value / 10.0
            
            temperatures[i + 1] = {
                'raw': raw_value,
                'celsius': temperature,
                'fahrenheit': (temperature * 9/5) + 32
            }
    
    except ModbusException as e:
        print(f"ERROR: MODBUS exception: {e}")
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
    
    return temperatures

def display_temperatures(temperatures):
    """Display temperature readings in a formatted way"""
    print("\n" + "="*60)
    print("DS18B20 Temperature Sensor Status")
    print("="*60)
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("-"*60)
    
    if not temperatures:
        print("No sensor data available")
        return
    
    print(f"{'Sensor':<10} {'Raw Value':<12} {'°C':<12} {'°F':<12} {'Status'}")
    print("-"*60)
    
    for sensor_num in range(1, 9):
        if sensor_num in temperatures:
            data = temperatures[sensor_num]
            temp_c = data['celsius']
            temp_f = data['fahrenheit']
            raw = data['raw']
            
            # Determine sensor status
            if temp_c < -55 or temp_c > 125:
                status = "OUT OF RANGE"
            elif raw == 0 or raw == 0xFFFF:
                status = "NOT CONNECTED"
            else:
                status = "OK"
            
            print(f"Sensor {sensor_num:<3} {raw:<12} {temp_c:>6.1f}°C     {temp_f:>6.1f}°F     {status}")
        else:
            print(f"Sensor {sensor_num:<3} {'N/A':<12} {'N/A':<12} {'N/A':<12} {'NO DATA'}")
    
    print("="*60 + "\n")

def main():
    """Main monitoring loop"""
    print("Temperature Monitor Starting...")
    print(f"Serial Port: {SERIAL_PORT}")
    print(f"MODBUS Address: {MODBUS_ADDRESS}")
    print(f"Baudrate: {BAUDRATE}")
    
    client = init_modbus_client()
    
    if not client.connect():
        print(f"ERROR: Failed to connect to {SERIAL_PORT}")
        print("Please check:")
        print("  - Serial port is correct")
        print("  - USB to RS485 adapter is connected")
        print("  - RS485 wiring (A+, B-, GND)")
        print("  - Device power (6-24V DC)")
        sys.exit(1)
    
    print("Connected successfully!\n")
    
    try:
        while True:
            temperatures = read_temperature_sensors(client, NUM_SENSORS)
            display_temperatures(temperatures)
            
            # Read at configured interval
            time.sleep(POLL_INTERVAL)
    
    except KeyboardInterrupt:
        print("\nShutting down temperature monitor...")
    
    finally:
        client.close()
        print("Connection closed.")

if __name__ == "__main__":
    main()
