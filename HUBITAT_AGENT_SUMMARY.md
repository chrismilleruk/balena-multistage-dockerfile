# Hubitat TRV Integration - Implementation Summary

## Overview

A complete Docker-based integration layer (`hubitat-agent`) has been added to ingest temperature and status data from Hubitat Elevation smart thermostats (TRVs) and store it in TimescaleDB alongside wired sensor data.

## Architecture

```
Hubitat Maker API
       ↓
hubitat-agent (Docker service)
   ├─ Poll mode: Continuous GET requests every 60s
   └─ Server mode: Listen for webhook POSTs
       ↓
TimescaleDB (PostgreSQL + TimescaleDB extension)
   └─ trv_temperatures (hypertable, partitioned by time)
       ↓
Grafana / Applications (query dashboards)
```

## Files Added/Modified

### New Files

#### Core Agent Code
- **`hubitat_agent/main.py`** - Main entry point supporting poll and server modes
- **`hubitat_agent/hubitat_client.py`** - HTTP API client and TRV data extraction logic
- **`hubitat_agent/db.py`** - PostgreSQL/TimescaleDB write helpers
- **`hubitat_agent/migrations.py`** - Database migration runner (runs on service startup)
- **`hubitat_agent/Dockerfile`** - Multi-stage Docker build (Python 3.11 slim)
- **`hubitat_agent/requirements-hubitat.txt`** - Dependencies: requests, psycopg2-binary, Flask
- **`hubitat_agent/README.md`** - Complete documentation for the agent

#### Testing
- **`hubitat_agent/test_hubitat_client.py`** - Unit tests for JSON parsing and field extraction
- **`hubitat_agent/smoke_test.py`** - Integration smoke test (parsing, DB connection, insert/query)

#### Database
- **`migrations/001_create_trv_temperatures.sql`** - TimescaleDB table schema and hypertable setup

#### Configuration & Documentation
- **`.env.example-hubitat`** - Example environment variables template
- **`TEMPERATURE_SETUP.md`** - Updated with Hubitat TRV section (quick start, modes, queries, troubleshooting)

### Modified Files
- **`docker-compose.yml`** - Added `hubitat-agent` service with environment vars and depends_on
- **`docker-compose.dev.yml`** - Added `hubitat-agent` service (same as production)
- **`hubitat_agent/main.py`** - Updated to call `run_migrations()` at startup

## Key Features

### 1. Dual Mode Operation

**Poll Mode (Default)**
- Continuously fetches all Hubitat devices at configurable interval (default 60s)
- Simple setup, no Hubitat configuration needed
- Slight latency (up to poll interval)

**Server Mode**
- Listens for POST webhooks from Hubitat Maker API
- Real-time data ingestion
- Requires Hubitat network configuration

### 2. Automatic Database Setup

- Migration runner (`migrations.py`) executes on container startup
- Creates `trv_temperatures` table and TimescaleDB hypertable automatically
- No manual SQL commands needed

### 3. Robust Data Extraction

- Tolerates missing optional fields (graceful degradation)
- Type conversion for numeric fields (float/int)
- Stores full device JSON for debugging
- Logs parsing errors and continues

### 4. TRV Data Captured

| Field | Type | Source | Example |
|-------|------|--------|---------|
| device_id | text | device.id | "45" |
| label | text | device.label | "Good Room" |
| room | text | device.room | "Good room" |
| temperature | float | attributes.temperature | 17.6 |
| setpoint | float | attributes.thermostatSetpoint | 19.0 |
| battery | int | attributes.battery | 100 |
| health_status | text | attributes.healthStatus | "online" |
| operating_state | text | attributes.thermostatOperatingState | "heating" |
| raw | jsonb | full device object | {...} |

## Usage Examples

### Quick Start

```bash
# 1. Set Hubitat API URL
export HUBITAT_API_URL="http://192.168.10.109/apps/api/50/devices/all?access_token=YOUR_TOKEN"

# 2. Start services
docker-compose up -d timescaledb hubitat-agent

# 3. Check logs
docker-compose logs -f hubitat-agent

# 4. Query data
docker-compose exec timescaledb psql -U sensor_user -d sensor_data -c \
  "SELECT * FROM trv_temperatures ORDER BY time DESC LIMIT 10;"
```

### Configuration via Environment

```bash
# In docker-compose or .env
MODE=poll                          # poll or server
HUBITAT_API_URL=http://...        # Full URL with token
POLL_INTERVAL_SECONDS=60          # How often to poll
TIMESCALEDB_URL=postgresql://...  # DB connection
```

### Query Examples

**Recent temperatures by device:**
```sql
SELECT device_id, label, room, temperature, setpoint, battery, time
FROM trv_temperatures
WHERE time > now() - interval '1 hour'
ORDER BY device_id, time DESC;
```

**Average temp by room (15-min buckets):**
```sql
SELECT 
  room,
  AVG(temperature) as avg_temp,
  time_bucket('15 minutes', time) as bucket
FROM trv_temperatures
WHERE time > now() - interval '24 hours'
GROUP BY room, bucket
ORDER BY bucket DESC;
```

**Device health status:**
```sql
SELECT DISTINCT device_id, label, health_status, MAX(time)
FROM trv_temperatures
WHERE time > now() - interval '1 hour'
GROUP BY device_id, label, health_status;
```

## Testing

### Unit Tests
```bash
pip install pytest
cd hubitat_agent
pytest test_hubitat_client.py -v
```

Tests cover:
- Happy path: full device object with all fields
- Missing fields: optional attributes handled gracefully
- Invalid types: conversion failures return None
- Edge cases: no device_id, empty attributes, null values

### Smoke Test
```bash
# Requires DB connection
export TIMESCALEDB_URL="postgresql://sensor_user:sensor_password@localhost:5432/sensor_data"
python hubitat_agent/smoke_test.py
```

Verifies:
1. ✓ Field extraction works
2. ✓ Database connection succeeds
3. ✓ Table schema exists
4. ✓ Data insert and query work end-to-end

## Deployment Checklist

- [ ] Obtain Hubitat Maker API URL and access token
- [ ] Set `HUBITAT_API_URL` (or `HUBITAT_HOST` + `HUBITAT_TOKEN`) in environment
- [ ] Set `MODE` to `poll` (or `server` if configuring webhooks)
- [ ] Ensure `TIMESCALEDB_URL` points to correct database
- [ ] Run `docker-compose up -d` to start all services
- [ ] Wait 10-20 seconds for migrations to complete
- [ ] Query `trv_temperatures` table to verify data is appearing
- [ ] Monitor logs: `docker-compose logs -f hubitat-agent`
- [ ] Add TRV data panels to Grafana dashboard

## Supported Device Types

Any Hubitat device with these attributes will work:
- `attributes.temperature` (required for meaningful data)
- `attributes.thermostatSetpoint`
- `attributes.battery` (for battery-powered devices)
- `attributes.healthStatus`
- `attributes.thermostatOperatingState`

**Known compatible devices:**
- Sonoff TRVZB (Zigbee)
- Sonoff TRV (Z-Wave)
- Standard SmartThings-compatible thermostats

## Monitoring & Observability

### Service Health
```bash
docker-compose ps  # Check service status

docker-compose logs hubitat-agent  # View logs
```

### Database Activity
```bash
psql -U sensor_user -d sensor_data

SELECT COUNT(*) FROM trv_temperatures;
SELECT MAX(time) FROM trv_temperatures;
SELECT DISTINCT device_id FROM trv_temperatures;
```

### Performance
- Default insert rate: 1 device per 60 seconds = 1440 rows/device/day
- 3 devices ≈ 4320 rows/day, 130K rows/month
- TimescaleDB compression keeps storage efficient

## Future Enhancements

- [ ] Change detection (only insert on value change)
- [ ] Webhook signature verification for server mode
- [ ] Exponential backoff for transient HTTP errors
- [ ] Prometheus metrics endpoint
- [ ] Support for other device types (lights, switches, etc.)
- [ ] Automatic Grafana dashboard provisioning
- [ ] Data retention policies (compress old data)

## Troubleshooting Quick Reference

| Problem | Cause | Solution |
|---------|-------|----------|
| "HUBITAT_API_URL must be provided" | Env var not set | Export `HUBITAT_API_URL` or set in docker-compose |
| "Failed to fetch devices" | API unreachable or token invalid | Test endpoint with curl, verify token in Hubitat app |
| "No data in trv_temperatures" | API fetch failing or DB down | Check service logs, verify DB connection |
| "Connection refused" to TimescaleDB | DB not running | `docker-compose up -d timescaledb` |
| Service crashes on startup | Migration failed | Check DB has TimescaleDB extension enabled |

## Documentation Locations

- **Agent specifics:** `hubitat_agent/README.md`
- **Project integration:** `TEMPERATURE_SETUP.md` (Hubitat TRV section)
- **Configuration template:** `.env.example-hubitat`
- **Database schema:** `migrations/001_create_trv_temperatures.sql`

## Integration with Existing Sensors

The `hubitat-agent` writes to the same TimescaleDB as the wired `temp-monitor` service:

- Both store time-series data in the same database
- Different tables: `sensor_readings` (wired) vs `trv_temperatures` (wireless)
- Can query and visualize together in Grafana
- Shared authentication and network (via Docker compose)

This allows a unified temperature monitoring solution combining wired and wireless devices.
