# ✅ Hubitat TRV Integration - Ready to Deploy

## What Was Built

A complete **hubitat-agent** Docker service that:

1. **Fetches TRV data from Hubitat** via the Maker API (poll or webhook modes)
2. **Parses and validates** temperature, setpoint, battery, health status, operating state
3. **Stores in TimescaleDB** in a new `trv_temperatures` hypertable
4. **Auto-runs migrations** on container startup (no manual SQL needed)
5. **Works on Balena devices** via docker-compose push

## What's Ready to Test

### Files Added

```
hubitat_agent/
  ├─ main.py                 (poll/server modes, calls migrations on startup)
  ├─ hubitat_client.py       (HTTP API fetch + TRV field extraction)
  ├─ db.py                   (PostgreSQL inserts)
  ├─ migrations.py           (auto-runs SQL migrations)
  ├─ Dockerfile              (Python 3.11-slim, ~200MB)
  ├─ requirements-hubitat.txt (requests, psycopg2, Flask, pytest)
  ├─ README.md               (full agent documentation)
  ├─ test_hubitat_client.py  (unit tests for parsing)
  └─ smoke_test.py           (integration test)

migrations/
  └─ 001_create_trv_temperatures.sql  (creates table + hypertable + index)

docs/
  ├─ HUBITAT_AGENT_SUMMARY.md         (overview & examples)
  ├─ HUBITAT_AGENT_TESTING.md         (balena testing guide)
  ├─ TEMPERATURE_SETUP.md             (updated with Hubitat section)
  └─ .env.example-hubitat             (config template)

docker-compose.yml & docker-compose.dev.yml
  └─ hubitat-agent service (with MODE, POLL_INTERVAL, API URL env vars)
```

### Key Facts

- **Migration:** Creates `trv_temperatures` table with 10 columns (time, device_id, label, room, temperature, setpoint, battery, health_status, operating_state, raw)
- **Build context:** Project root (so migrations/ is accessible)
- **Startup:** Runs migrations.py → run_migrations() before entering poll/server loop
- **No manual SQL:** All schema setup happens in container on first start
- **Error handling:** Logs failures, continues on parse errors, retries on transient failures

## How to Test on Balena Device

### Step 1: Build (optional—balena handles this)
```bash
docker-compose build hubitat-agent
```

### Step 2: Push to Balena Device
```bash
balena push c45f46e.local
```

### Step 3: Set Environment Variables

Via SSH:
```bash
balena ssh c45f46e.local
# Set via balena Cloud UI, or environment on device
```

Or via balena Cloud UI (recommended):
1. Go to device page
2. Variables section
3. Add:
   - `HUBITAT_API_URL` = `http://192.168.10.109/apps/api/50/devices/all?access_token=YOUR_TOKEN`
   - `MODE` = `poll` (or `server`)
   - `POLL_INTERVAL_SECONDS` = `60`

### Step 4: Watch Logs
```bash
balena logs c45f46e.local -f hubitat-agent
```

Expected output:
```
Running migration: 001_create_trv_temperatures.sql
All migrations completed successfully
Starting poll loop (interval=60s)
Inserted 3 device rows
Inserted 3 device rows
...
```

### Step 5: Verify Data
```bash
balena ssh c45f46e.local
balena exec timescaledb psql -U sensor_user -d sensor_data -c \
  "SELECT device_id, label, temperature, setpoint, battery FROM trv_temperatures ORDER BY time DESC LIMIT 5;"
```

Should see rows like:
```
 device_id |    label    | temperature | setpoint | battery
-----------+-------------+-------------+----------+---------
 45        | Good Room   |        17.6 |     19.0 |     100
 21        | Snug TRVZB  |        18.9 |     19.0 |     100
 14        | OPL TRVZB   |        19.5 |     19.0 |      59
```

## Troubleshooting Checklist

- [ ] Service builds without errors: `docker-compose build hubitat-agent`
- [ ] Dockerfile has correct COPY paths for migrations
- [ ] `HUBITAT_API_URL` is set and valid
- [ ] `TIMESCALEDB_URL` points to correct database (default in compose works)
- [ ] TimescaleDB is running: `balena ls c45f46e.local`
- [ ] Logs show "All migrations completed successfully"
- [ ] Logs show "Inserted X device rows" (not 0)
- [ ] `trv_temperatures` table exists and has rows

## Quick Commands Reference

```bash
# Build
docker-compose build hubitat-agent

# Push to device
balena push c45f46e.local

# Watch logs
balena logs c45f46e.local -f hubitat-agent

# SSH to device
balena ssh c45f46e.local

# Query data on device
balena exec timescaledb psql -U sensor_user -d sensor_data

# Run agent once (for testing)
balena exec hubitat-agent bash -c "RUN_ONCE=true python main.py"
```

## Testing Modes

### Poll Mode (Default)
- Fetches all devices every 60 seconds (configurable)
- `MODE=poll POLL_INTERVAL_SECONDS=60`
- Best for getting started

### Server Mode
- Listens on port 8080 for POST webhooks
- `MODE=server HOST=0.0.0.0 PORT=8080`
- Configure Hubitat Maker API to POST to: `http://<device-ip>:8080/hubitat/events`
- Real-time updates (no polling overhead)

### One-Shot Mode
- Runs once and exits (useful for debugging)
- `RUN_ONCE=true python main.py`

## Supported Devices

Any Hubitat device with a `temperature` attribute:
- ✓ Sonoff TRVZB (Zigbee)
- ✓ Sonoff TRV (Z-Wave)
- ✓ Standard SmartThings thermostats
- ✓ Any device with thermostat capabilities

## What Happens on First Run

1. Container starts
2. `main.py` runs
3. Calls `run_migrations()` → connects to DB → executes `001_create_trv_temperatures.sql`
4. Migration creates table, hypertable, and index (or skips if already exists)
5. Enters poll loop → fetches Hubitat API every 60 seconds → inserts rows to DB
6. Data is queryable immediately

## No Manual Steps Needed For Schema

Unlike traditional apps, you **don't need to** manually run SQL migrations. The container handles it automatically on startup via the `migrations.py` module.

---

**Ready to push!** Follow "How to Test on Balena Device" section above. 🚀

For detailed docs, see:
- `hubitat_agent/README.md` - Full agent documentation
- `HUBITAT_AGENT_TESTING.md` - Balena testing guide
- `TEMPERATURE_SETUP.md` - Integration with existing sensors
