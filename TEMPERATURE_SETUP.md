# Temperature Monitoring Setup

This project monitors 8 DS18B20 temperature sensors connected via an R4DCB08 8-Bit RS485 Temperature Receiver using MODBUS RTU protocol.

## Hardware Requirements

### Components
1. **USB to RS485 Converter** - Waveshare USB TO RS485 (B) with CH343G chip
2. **Temperature Receiver** - DONGKER R4DCB08 8Bit RS485 Temperature Receiver (MODBUS)
3. **Temperature Sensors** - Up to 8 × DS18B20 waterproof temperature sensors (HALJIA or compatible)

### Wiring

#### USB to RS485 Adapter to R4DCB08
```
USB to RS485        R4DCB08
────────────        ───────
    A+      ────────  A
    B-      ────────  B
    GND     ────────  GND
```

#### Power for R4DCB08
- Connect **V+** to DC 6-24V (typically 12V or 24V)
- Connect **GND** to power supply ground

#### DS18B20 Sensors to R4DCB08
Each DS18B20 sensor connects to the numbered sensor ports on the R4DCB08:
- **Red wire (VCC)** → Sensor power terminal
- **Yellow wire (Data)** → Sensor data terminal  
- **Black wire (GND)** → Sensor ground terminal

The R4DCB08 supports up to 8 sensors. Each sensor is automatically assigned an address (1-8).

## Software Configuration

### Environment Variables

You can configure the temperature monitor using balena environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `SERIAL_PORT` | `/dev/ttyUSB0` | Serial port for USB to RS485 adapter |
| `MODBUS_ADDRESS` | `1` | MODBUS device address of R4DCB08 |
| `BAUDRATE` | `9600` | Serial communication baudrate |
| `PARITY` | `N` | Parity bit (N=None, E=Even, O=Odd) |
| `STOPBITS` | `1` | Number of stop bits |
| `BYTESIZE` | `8` | Number of data bits |
| `TIMEOUT` | `3` | Communication timeout in seconds |
| `NUM_SENSORS` | `8` | Number of temperature sensors to read |
| `TEMP_START_REGISTER` | `0` | Starting MODBUS register for temperature data |
| `POLL_INTERVAL` | `5` | Seconds between temperature readings |

### Setting Variables in Balena Cloud

1. Navigate to your device or fleet in balena Cloud
2. Go to **Variables** section
3. Add variables with appropriate values
4. Changes take effect after the container restarts

### Local Development

For local testing, you can modify `config.env` or export environment variables before running.

## Deployment

### Production Deployment to Balena Device

```bash
# From the project directory
balena push <app-name>
```

### Local Development Mode

```bash
# Push to local device (uses dev stage with live reload)
balena push <device-ip>.local
```

### Building Specific Stages

```bash
# Build production stage
balena build --target prod -t temp-monitor:prod .

# Build dev stage
balena build --target dev -t temp-monitor:dev .
```

## Temperature Monitor Output

The application displays temperature readings every 5 seconds (configurable):

```
============================================================
DS18B20 Temperature Sensor Status
============================================================
Timestamp: 2025-11-11 22:30:15
------------------------------------------------------------
Sensor     Raw Value    °C           °F           Status
------------------------------------------------------------
Sensor 1   245          24.5°C       76.1°F       OK
Sensor 2   230          23.0°C       73.4°F       OK
Sensor 3   255          25.5°C       77.9°F       OK
Sensor 4   0            0.0°C        32.0°F       NOT CONNECTED
Sensor 5   220          22.0°C       71.6°F       OK
Sensor 6   N/A          N/A          N/A          NO DATA
Sensor 7   N/A          N/A          N/A          NO DATA
Sensor 8   N/A          N/A          N/A          NO DATA
============================================================
```

### Status Indicators

- **OK** - Sensor connected and reading within valid range (-55°C to 125°C)
- **NOT CONNECTED** - Sensor slot configured but no sensor detected (raw value = 0 or 0xFFFF)
- **OUT OF RANGE** - Temperature reading outside DS18B20 spec range
- **NO DATA** - MODBUS communication error or sensor not responding

## Troubleshooting

### No Connection to Serial Port

**Error:** `Failed to connect to /dev/ttyUSB0`

**Solutions:**
1. Verify USB to RS485 adapter is plugged in
2. Check device permissions: `ls -l /dev/ttyUSB*`
3. Try different serial port (may be `/dev/ttyUSB1`, `/dev/ttyACM0`, etc.)
4. Update `SERIAL_PORT` environment variable if needed
5. Ensure container has privileged access (already configured in docker-compose.yml)

### All Sensors Show "NOT CONNECTED"

**Causes:**
- DS18B20 sensors not connected to R4DCB08
- R4DCB08 not powered (needs 6-24V DC)
- Wrong MODBUS address

**Solutions:**
1. Check R4DCB08 power LED
2. Verify sensor wiring (Red=VCC, Yellow=Data, Black=GND)
3. Check MODBUS address - try updating `MODBUS_ADDRESS` environment variable
4. Test with a known working sensor first

### MODBUS Communication Errors

**Error:** `MODBUS read failed` or `MODBUS exception`

**Solutions:**
1. Verify RS485 wiring (A+ and B- not swapped)
2. Check baudrate matches R4DCB08 configuration (default 9600)
3. Ensure proper RS485 termination (120Ω resistor if needed for long cables)
4. Try lowering baudrate or increasing timeout

### Incorrect Temperature Readings

**Issue:** Temperature values seem wrong

**Solutions:**
1. R4DCB08 may use different encoding (0.1°C units vs direct celsius)
2. Check manufacturer documentation for register format
3. Modify conversion formula in `temp_monitor.py` if needed:
   ```python
   # Current: temp = raw_value / 10.0
   # Alternative: temp = raw_value  (for direct celsius)
   ```

## Testing Without Hardware

To test the application without actual hardware:

1. Use a USB-to-RS485 loopback adapter
2. Use MODBUS simulation software
3. Comment out the connection check in `temp_monitor.py` for dry-run testing

## DS18B20 Specifications

- **Temperature Range:** -55°C to +125°C
- **Accuracy:** ±0.5°C (-10°C to +85°C)
- **Resolution:** 9-12 bits (programmable)
- **Protocol:** 1-Wire digital interface
- **Power:** 3.0-5.5V DC

## R4DCB08 MODBUS Registers

The R4DCB08 typically uses MODBUS function 03 (Read Holding Registers):

- **Registers 0-7:** Temperature readings for sensors 1-8
- **Register format:** Signed 16-bit integer (typically 0.1°C units)

*Note: Exact register mapping may vary by firmware version. Consult manufacturer documentation or contact seller for AT/UART command reference.*

## Support & Resources

- [Waveshare USB TO RS485 (B) Wiki](https://www.waveshare.com/wiki/USB_TO_RS485_(B))
- See `DEVICES.md` for complete hardware specifications
- For R4DCB08 AT/UART commands, contact DONGKER seller post-purchase

---

# Hubitat TRV Integration

In addition to wired temperature sensors, you can integrate smart TRV (Thermostat Radiator Valve) devices from Hubitat Elevation using the `hubitat-agent` service.

## Overview

The `hubitat-agent` service fetches thermostat data from Hubitat's Maker API and stores it in the same TimescaleDB database alongside sensor readings. This allows you to:

- Monitor setpoints and actual temperatures from Zigbee/Z-Wave TRV devices
- Track battery levels of wireless thermostats
- Store device health status and operating state
- Query and visualize TRV data alongside wired sensor data in Grafana

## Quick Start

### 1. Get Your Hubitat API Endpoint

In Hubitat Elevation:
1. Go to **Apps** → **Maker API**
2. Create a new access token (or use existing)
3. Get the endpoint URL:
   ```
   http://192.168.10.109/apps/api/50/devices/all?access_token=cab9d803-e74b-443d-a81c-bba57d8b274b
   ```

### 2. Configure Environment Variables

Create or update `.env` in the project root with:

```bash
# Hubitat API (choose one method)
HUBITAT_API_URL=http://192.168.10.109/apps/api/50/devices/all?access_token=YOUR_TOKEN_HERE

# OR use host + token:
# HUBITAT_HOST=192.168.10.109
# HUBITAT_TOKEN=YOUR_TOKEN_HERE

# Agent mode: 'poll' for continuous polling, 'server' for webhooks
HUBITAT_AGENT_MODE=poll

# Poll interval in seconds (default 60)
HUBITAT_POLL_INTERVAL=60
```

Alternatively, set environment variables directly in balena Cloud:
1. Navigate to your device/fleet in balena Cloud
2. Go to **Environment Variables**
3. Add `HUBITAT_API_URL`, `HUBITAT_AGENT_MODE`, etc.

### 3. Start the Service

```bash
# If running locally with docker-compose
docker-compose up -d hubitat-agent

# For balena, push your changes:
balena push <app-name>
```

### 4. Verify Data

Check that data is being inserted:

```bash
docker-compose exec timescaledb psql -U sensor_user -d sensor_data -c \
  "SELECT * FROM trv_temperatures ORDER BY time DESC LIMIT 10;"
```

You should see rows with device_id, label, room, temperature, setpoint, battery, etc.

## Configuration Modes

### Poll Mode (Recommended for Most Users)

The agent continuously fetches all Hubitat devices at a fixed interval:

```bash
MODE=poll
POLL_INTERVAL_SECONDS=60  # Fetch every 60 seconds
```

- **Pros:** Simple, no Hubitat network changes needed
- **Cons:** Regular network traffic, slight latency (up to `POLL_INTERVAL_SECONDS`)

### Server Mode (Webhook)

The agent listens for POST events from Hubitat's Maker API:

```bash
MODE=server
HOST=0.0.0.0
PORT=8080
```

Then configure Hubitat to POST device events to:
```
http://<your-agent-host>:8080/hubitat/events
```

- **Pros:** Real-time updates, minimal polling overhead
- **Cons:** Requires Hubitat network configuration, may need firewall rules

## Querying TRV Data

### Recent Readings by Device

```sql
SELECT device_id, label, room, temperature, setpoint, battery, health_status, operating_state, time
FROM trv_temperatures
WHERE time > now() - interval '1 hour'
ORDER BY device_id, time DESC;
```

### Average Temperature by Room

```sql
SELECT 
  room,
  device_id,
  label,
  AVG(temperature) as avg_temperature,
  AVG(setpoint) as avg_setpoint,
  MAX(battery) as battery_level,
  time_bucket('15 minutes', time) as bucket
FROM trv_temperatures
WHERE time > now() - interval '24 hours'
GROUP BY room, device_id, label, bucket
ORDER BY bucket DESC, room;
```

### Device Health Status

```sql
SELECT DISTINCT
  device_id,
  label,
  room,
  health_status,
  MAX(time) as last_update
FROM trv_temperatures
WHERE time > now() - interval '1 hour'
GROUP BY device_id, label, room, health_status
ORDER BY room, device_id;
```

### Low Battery Alert

```sql
SELECT device_id, label, room, battery, time
FROM trv_temperatures
WHERE battery IS NOT NULL AND battery < 20
  AND time > now() - interval '1 day'
ORDER BY battery ASC, time DESC;
```

## Supported Device Types

The agent extracts temperature data from any Hubitat device that has:
- `attributes.temperature` - Current measured temperature
- `attributes.thermostatSetpoint` - Target temperature setpoint
- `attributes.battery` - Battery percentage (wireless devices)
- `attributes.healthStatus` - Device online/offline status
- `attributes.thermostatOperatingState` - Current heating/cooling/idle state

### Known Compatible Devices

- **Sonoff TRVZB** - Zigbee Thermostatic Radiator Valve
- **Sonoff TRV** - Z-Wave variant
- Standard Zigbee/Z-Wave thermostats with SmartThings device handlers

If you have a different device type, check that it has the attributes above, or contact support.

## Troubleshooting

### Service won't start: "HUBITAT_API_URL or HUBITAT_HOST+HUBITAT_TOKEN must be provided"

**Solution:** Ensure at least one of the following is set in environment:
- `HUBITAT_API_URL` (full URL with token), OR
- Both `HUBITAT_HOST` and `HUBITAT_TOKEN`

### Service crashes: "Failed to fetch devices"

**Possible causes:**
1. Incorrect API URL or token
2. Hubitat hub is offline or unreachable
3. Network connectivity issue

**Debug:**
```bash
# Test the API endpoint manually
curl "http://192.168.10.109/apps/api/50/devices/all?access_token=YOUR_TOKEN"

# Check service logs
docker-compose logs hubitat-agent
```

### No data in `trv_temperatures` table

1. Verify the service is running: `docker-compose ps`
2. Check logs for errors: `docker-compose logs hubitat-agent`
3. Verify database connectivity: `docker-compose logs timescaledb`
4. Manually test one poll:
   ```bash
   docker-compose exec hubitat-agent bash
   RUN_ONCE=true python main.py
   ```

### "MODBUS" or "Device" errors in logs

These come from the wired temperature sensor service, not the Hubitat agent. See the above sections for MODBUS troubleshooting.

## Visualization in Grafana

Once data is stored in TimescaleDB, you can create Grafana dashboards:

1. Open Grafana: `http://localhost:3000` (username: admin, password: admin)
2. Add a new panel querying `trv_temperatures`
3. Example queries:
   - **Gauge:** `SELECT temperature FROM trv_temperatures WHERE device_id = '45' ORDER BY time DESC LIMIT 1`
   - **Time series:** `SELECT time, temperature FROM trv_temperatures WHERE device_id = '45' AND time > now() - interval '24 hours'`
   - **Table:** Select all columns for detailed view

See `TIMESCALEDB_SETUP.md` for more Grafana setup details.

## Advanced: Adding Custom Fields

If you want to capture additional device attributes:

1. Edit `hubitat_agent/hubitat_client.py` in the `extract_trv_fields()` function
2. Add your new field to the return dictionary
3. Update `migrations/001_create_trv_temperatures.sql` to add the column
4. Restart the service and the migration will run automatically

Example:

```python
# In hubitat_client.py, extract_trv_fields()
return {
    # ... existing fields ...
    "my_custom_field": attributes.get("myCustomAttribute"),
}
```

```sql
-- In migrations/001_create_trv_temperatures.sql
ALTER TABLE trv_temperatures ADD COLUMN my_custom_field text;
```

## Performance & Limits

- **Polling:** Default 60 seconds per poll. Adjust `POLL_INTERVAL_SECONDS` as needed.
  - 60 seconds = 1440 rows/device/day
  - For 3 devices: ~4320 rows/day, ~130K rows/month
- **Storage:** TimescaleDB compression helps keep storage efficient
- **API Rate Limits:** Hubitat Maker API typically allows ~1 request/second. Polling at 60-second intervals is well within limits.

For more details, see `hubitat_agent/README.md`.

````
