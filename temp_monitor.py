#!/usr/bin/env python3
"""
Temperature Monitor for R4DCB08 8-Bit RS485 Temperature Receiver
Reads up to 8 DS18B20 sensors via MODBUS RTU protocol
Stores data in TimescaleDB
"""

import time
import sys
import os
from datetime import datetime
from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException
import psycopg2
from psycopg2.extras import execute_batch

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
POLL_INTERVAL = int(os.getenv('POLL_INTERVAL', '15'))

# Optional: registers where DS18B20 ROM codes are exposed by the device
# If your MODBUS device exposes the 8-byte ROM per sensor in holding registers,
# set ROM_START_REGISTER and ROM_REGISTERS_PER_SENSOR accordingly.
ROM_START_REGISTER_ENV = os.getenv('ROM_START_REGISTER', '')
ROM_START_REGISTER = int(ROM_START_REGISTER_ENV) if ROM_START_REGISTER_ENV != '' else None
ROM_REGISTERS_PER_SENSOR = int(os.getenv('ROM_REGISTERS_PER_SENSOR', '4'))  # 8 bytes -> 4 registers

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://sensor_user:sensor_password@localhost:5432/sensor_data')

def init_database():
    """Initialize database connection and create table if needed"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Create table for sensor data with TimescaleDB hypertable
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensor_readings (
                time TIMESTAMPTZ NOT NULL,
                sensor_id INTEGER NOT NULL,
                temperature_celsius DOUBLE PRECISION NOT NULL,
                temperature_fahrenheit DOUBLE PRECISION NOT NULL,
                raw_value INTEGER
            );
        """)
        
        # Convert to hypertable if not already done
        try:
            cursor.execute("""
                SELECT create_hypertable('sensor_readings', 'time', if_not_exists => TRUE);
            """)
        except Exception as e:
            # Table may already be a hypertable
            pass
        
        # Create index for better query performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS sensor_readings_sensor_id_time 
            ON sensor_readings (sensor_id, time DESC);
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        print("Database initialized successfully")
        return True
    except Exception as e:
        print(f"ERROR: Failed to initialize database: {e}")
        return False


def read_sensor_roms(client, start_register, num_sensors, registers_per_sensor=4):
    """Read ROM codes for DS18B20 sensors exposed as holding registers.

    This is device-specific. Many R4DCB08-style devices may expose the 8-byte
    ROM code (64-bit) per sensor across consecutive registers. Each register
    is 2 bytes, so 4 registers per sensor.

    Returns: dict mapping port_number (1-based) -> rom_hex (string) on success.
    If read fails or ROM_START_REGISTER not configured, returns empty dict.
    """
    roms = {}
    if start_register is None:
        return roms

    try:
        count = num_sensors * registers_per_sensor
        result = client.read_holding_registers(start_register, count=count, device_id=MODBUS_ADDRESS)
        if not result or getattr(result, "isError", lambda: False)():
            print(f"INFO: ROM read failed or not available at register {start_register}: {result}")
            return roms

        regs = result.registers
        for i in range(num_sensors):
            start = i * registers_per_sensor
            chunk = regs[start:start + registers_per_sensor]
            # Convert registers (16-bit) into bytes. Assume big-endian register order
            b = bytearray()
            for reg in chunk:
                high = (reg >> 8) & 0xFF
                low = reg & 0xFF
                b.append(high)
                b.append(low)

            # ROM is 8 bytes; trim/pad if necessary
            rom_bytes = bytes(b[:8])
            roms[i + 1] = rom_bytes.hex()

    except Exception as e:
        print(f"ERROR: Failed reading sensor ROMs: {e}")

    return roms


def ensure_sensors_table_and_rows():
    """Create sensors table and ensure rows exist for ports 1..NUM_SENSORS.

    The `id` column is the durable sensor identifier and by default we create
    entries with id == port_number to maintain backwards compatibility with
    existing `sensor_readings.sensor_id` values.
    """
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensors (
                id INTEGER PRIMARY KEY,
                port_number INTEGER NOT NULL,
                rom_code TEXT UNIQUE,
                calibration_offset_raw INTEGER DEFAULT 0
            );
        """)

        # Ensure rows exist for the current ports. Use id == port_number to avoid migration.
        for port in range(1, NUM_SENSORS + 1):
            cursor.execute(
                """
                INSERT INTO sensors (id, port_number)
                VALUES (%s, %s)
                ON CONFLICT (id) DO UPDATE SET port_number = EXCLUDED.port_number;
                """,
                (port, port)
            )

        # Index for lookups
        cursor.execute("CREATE INDEX IF NOT EXISTS sensors_port_number_idx ON sensors (port_number);")

        conn.commit()
        cursor.close()
        conn.close()
        print("Sensors table ensured")
        return True
    except Exception as e:
        print(f"ERROR: Failed to ensure sensors table: {e}")
        return False


def display_sensors_calibration():
    """Display the current sensors table (ids, offsets, ROM codes) for reference."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT id, port_number, rom_code, calibration_offset_raw FROM sensors ORDER BY id")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        print("\n" + "="*80)
        print("Sensor Configuration (Calibration Table)")
        print("="*80)
        if not rows:
            print("(No sensors configured)")
        else:
            print(f"{'ID':<4} {'Port':<6} {'Calibration Offset (raw 0.1°C)':<32} {'ROM Code':<20}")
            print("-"*80)
            for sensor_id, port, rom, offset_raw in rows:
                rom_str = rom if rom else "(not set)"
                offset_str = f"{int(offset_raw)}" if offset_raw else "0"
                print(f"{sensor_id:<4} {port:<6} {offset_str:<32} {rom_str:<20}")
        print("="*80 + "\n")
    except Exception as e:
        print(f"WARNING: Could not display sensors table: {e}\n")


def get_port_map():
    """Return a mapping of port_number -> (id, calibration_offset_raw) from sensors table.

    This is a small helper so the main loop can display adjusted temperatures
    using the same offsets that are applied when storing readings.
    """
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT id, port_number, calibration_offset_raw FROM sensors")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return {row[1]: (row[0], row[2] or 0) for row in rows}
    except Exception:
        return {}

def store_sensor_data(temperatures):
    """Store sensor readings in TimescaleDB"""
    if not temperatures:
        return False

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        # Load sensor registry mapping: port_number -> (id, calibration_offset_raw)
        cursor.execute("SELECT id, port_number, calibration_offset_raw FROM sensors")
        rows = cursor.fetchall()
        port_map = {row[1]: (row[0], row[2] or 0) for row in rows}

        data_to_insert = []
        timestamp = datetime.now()

        for sensor_port, data in temperatures.items():
            # Map port to sensor registry id, fallback to using the port number to preserve compatibility
            sensor_id, offset_raw = port_map.get(sensor_port, (sensor_port, 0))

            # Apply calibration offset to raw value FIRST, then convert to temperature
            raw_value = data['raw']
            adjusted_raw = raw_value + offset_raw
            
            # Convert adjusted raw value to temperature
            if adjusted_raw > 32767:  # If MSB is set (negative temperature)
                temp_c = (adjusted_raw - 65536) / 10.0
            else:
                temp_c = adjusted_raw / 10.0
            
            temp_f = (temp_c * 9/5) + 32

            data_to_insert.append((
                timestamp,
                sensor_id,
                temp_c,
                temp_f,
                raw_value
            ))

        # Insert data
        execute_batch(
            cursor,
            """
            INSERT INTO sensor_readings (time, sensor_id, temperature_celsius, temperature_fahrenheit, raw_value)
            VALUES (%s, %s, %s, %s, %s)
            """,
            data_to_insert
        )

        conn.commit()
        cursor.close()
        conn.close()
        print(f"Stored {len(data_to_insert)} sensor readings in database")
        return True
    except Exception as e:
        print(f"ERROR: Failed to store sensor data: {e}")
        return False

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
        result = client.read_holding_registers(TEMP_START_REGISTER, 
                                               count=num_sensors, 
                                               device_id=MODBUS_ADDRESS)
        
        # if result.isError():
        # result can be None with some transports/versions; guard against that
        if not result or getattr(result, "isError", lambda: False)():
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

def display_temperatures(temperatures, port_map=None):
    """Display temperature readings in the user's requested layout.

    Columns: [Raw][offset]  [raw_c] [true_c] [true_f] [status]
    """
    print("\n" + "="*80)
    print("DS18B20 Temperature Sensor Status")
    print("="*80)
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("-"*80)

    if not temperatures:
        print("No sensor data available")
        return

    print(f"{'Sensor':<8} {'Raw[offset]':<16} {'Raw °C':<12} {'True °C':<12} {'True °F':<12} {'Status'}")
    print("-"*80)

    for sensor_num in range(1, NUM_SENSORS + 1):
        if sensor_num in temperatures:
            data = temperatures[sensor_num]
            raw = data['raw']
            raw_c = data['celsius']

            # Determine sensor status based on unadjusted reading
            if raw_c < -55 or raw_c > 125:
                status = "OUT OF RANGE"
            elif raw == 0 or raw == 0xFFFF:
                status = "NOT CONNECTED"
            else:
                status = "OK"

            # Calibration offset for this port (raw units)
            offset = 0
            if port_map and sensor_num in port_map:
                _, offset = port_map[sensor_num]
            offset = int(offset or 0)

            # Adjusted/raw with offset applied and convert to °C/°F
            adjusted_raw = raw + offset
            if adjusted_raw > 32767:
                true_c = (adjusted_raw - 65536) / 10.0
            else:
                true_c = adjusted_raw / 10.0
            true_f = (true_c * 9/5) + 32

            # Format raw with signed offset like: 210[+2]
            sign = '+' if offset >= 0 else '-'
            raw_with_off = f"{raw}[{sign}{abs(offset)}]"

            print(f"Sensor {sensor_num:<3} {raw_with_off:<16} {raw_c:>6.1f}°C     {true_c:>6.1f}°C     {true_f:>6.1f}°F     {status}")
        else:
            print(f"Sensor {sensor_num:<3} {'N/A':<16} {'N/A':<12} {'N/A':<12} {'N/A':<12} {'NO DATA'}")

    print("="*80 + "\n")

def main():
    """Main monitoring loop"""
    print("Temperature Monitor Starting...")
    print(f"Serial Port: {SERIAL_PORT}")
    print(f"MODBUS Address: {MODBUS_ADDRESS}")
    print(f"Baudrate: {BAUDRATE}")
    print(f"Database URL: {DATABASE_URL}")
    print(f"Poll Interval: {POLL_INTERVAL}")
    
    # Initialize database
    print("\nInitializing database...")
    if not init_database():
        print("ERROR: Could not initialize database")
        sys.exit(1)
    
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
    # Ensure sensors registry exists (id == port_number by default for compat)
    if not ensure_sensors_table_and_rows():
        print("WARNING: Could not ensure sensors table; continuing but sensor mapping may not be available.")

    # Display current sensor configuration and calibration offsets
    display_sensors_calibration()

    # Optionally read ROM codes from device and update sensors table if ROM registers configured
    if ROM_START_REGISTER is not None:
        print(f"Attempting to read sensor ROMs starting at register {ROM_START_REGISTER}...")
        roms = read_sensor_roms(client, ROM_START_REGISTER, NUM_SENSORS, ROM_REGISTERS_PER_SENSOR)
        if roms:
            try:
                conn = psycopg2.connect(DATABASE_URL)
                cursor = conn.cursor()
                for port, rom in roms.items():
                    # Update rom_code only if present; allow overwrite if changed
                    cursor.execute(
                        "UPDATE sensors SET rom_code = %s WHERE port_number = %s",
                        (rom, port)
                    )
                    print(f"Updated ROM for port {port}: {rom}")
                conn.commit()
                cursor.close()
                conn.close()
            except Exception as e:
                print(f"ERROR: Failed to update sensors table with ROMs: {e}")
        else:
            print("No ROMs read from device (device may not expose them via MODBUS)")
    
    try:
        while True:
            temperatures = read_temperature_sensors(client, NUM_SENSORS)
            # Load current offsets for display (keeps display in sync with stored calibration)
            port_map = get_port_map()
            display_temperatures(temperatures, port_map)

            # Store data in database (store_sensor_data will still apply offsets when writing)
            store_sensor_data(temperatures)
            
            # Read at configured interval
            time.sleep(POLL_INTERVAL)
    
    except KeyboardInterrupt:
        print("\nShutting down temperature monitor...")
    
    finally:
        client.close()
        print("Connection closed.")

if __name__ == "__main__":
    main()
