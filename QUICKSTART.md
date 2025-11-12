# Temperature Monitor Quick Start

## Hardware Connections

```
[Raspberry Pi] ─USB─ [Waveshare USB-RS485] ─RS485─ [R4DCB08] ─1-Wire─ [8× DS18B20 Sensors]
                           (CH343G)                    (MODBUS)         (Temperature)
```

### Minimal Wiring
1. **USB to RS485 → R4DCB08:**
   - A+ → A
   - B- → B
   - GND → GND

2. **Power R4DCB08:**
   - V+ → 12V DC (or 6-24V)
   - GND → Power GND

3. **Connect DS18B20 sensors to R4DCB08 sensor ports (1-8)**

## Deploy to Balena

```bash
# Add remote
balena push <your-app-name>

# Or local mode
balena push <device-ip>.local
```

## View Logs

```bash
balena logs <device-uuid> --service temp-monitor --tail
```

## Configure (Optional)

Set environment variables in balena Cloud dashboard:

| Variable | Example | Purpose |
|----------|---------|---------|
| `SERIAL_PORT` | `/dev/ttyUSB0` | Serial device |
| `MODBUS_ADDRESS` | `1` | MODBUS slave ID |
| `POLL_INTERVAL` | `10` | Seconds between reads |
| `NUM_SENSORS` | `4` | Number of sensors (1-8) |

## Expected Output

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
...
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `Failed to connect` | Check USB cable, try `/dev/ttyUSB1` |
| All `NOT CONNECTED` | Check R4DCB08 power (6-24V DC) |
| `MODBUS exception` | Verify A+/B- not swapped |
| Wrong temps | Try `temp = raw_value` instead of `/10.0` |

See `TEMPERATURE_SETUP.md` for detailed documentation.
