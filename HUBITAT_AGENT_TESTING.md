# Hubitat Agent - Testing on Balena Device

## Local Testing Before Push

### 1. Verify Docker Build Locally

```bash
# Build the image
docker-compose build hubitat-agent

# Check for build errors
docker images | grep hubitat-agent
```

### 2. Quick Syntax Check

```bash
# Run Python syntax check on all agent files
python -m py_compile hubitat_agent/main.py
python -m py_compile hubitat_agent/hubitat_client.py
python -m py_compile hubitat_agent/db.py
python -m py_compile hubitat_agent/migrations.py
```

## Deploying to Balena Device (Local Mode)

### 1. Push with Local Mode

Assumes you have a balena device on your local network (e.g., `c45f46e.local`).

```bash
# Push in local mode (live reload, no rebuild required)
balena push c45f46e.local
```

### 2. Set Required Environment Variables

On the device (via `balena ssh` or balena Cloud):

```bash
balena ssh c45f46e.local

# Inside the device shell:
balena exec hubitat-agent bash

# Test the env is set:
echo $HUBITAT_API_URL
echo $TIMESCALEDB_URL
```

Or set via balena Cloud UI:
1. Go to your device page
2. Click "Variables"
3. Add:
   - `HUBITAT_API_URL`: `http://192.168.10.109/apps/api/50/devices/all?access_token=YOUR_TOKEN`
   - `MODE`: `poll`
   - `POLL_INTERVAL_SECONDS`: `60`

### 3. Monitor Service Logs

```bash
# Watch logs in real-time
balena logs c45f46e.local -f hubitat-agent

# Or SSH and check:
balena ssh c45f46e.local

# Inside device:
balena logs -f hubitat-agent
```

### 4. Verify Data Is Being Inserted

```bash
# SSH into device
balena ssh c45f46e.local

# Connect to database
balena exec timescaledb psql -U sensor_user -d sensor_data

# Query the table
SELECT * FROM trv_temperatures ORDER BY time DESC LIMIT 10;
```

## Troubleshooting on Balena Device

### Service won't start

```bash
# Check service status
balena ls c45f46e.local

# View service logs with errors
balena logs c45f46e.local hubitat-agent | grep -i error

# Full output:
balena logs c45f46e.local hubitat-agent
```

### Migration failed to run

Look for errors like `Migration failed:` in logs. Common causes:
- TimescaleDB not running: `balena ls c45f46e.local`
- Table already exists: Try `SELECT * FROM trv_temperatures;` to verify
- Bad migration SQL: Check syntax in `migrations/001_create_trv_temperatures.sql`

### Can't connect to API

```bash
# SSH to device and test manually
balena ssh c45f46e.local

# Test Hubitat API from device
curl "http://192.168.10.109/apps/api/50/devices/all?access_token=YOUR_TOKEN"

# If CORS/firewall: check routing
ping 192.168.10.109
```

### No database connection

```bash
# Check timescaledb service is running
balena ls c45f46e.local

# Test connection from hubitat-agent
balena exec hubitat-agent bash
psql postgresql://sensor_user:sensor_password@timescaledb:5432/sensor_data -c "SELECT 1;"
```

## One-Shot Test Run

Test that the agent can fetch and insert data without continuous polling:

```bash
# SSH to device
balena ssh c45f46e.local

# Run once and exit
balena exec hubitat-agent bash -c "RUN_ONCE=true python main.py"

# Check logs
balena logs c45f46e.local hubitat-agent

# Query result
balena exec timescaledb psql -U sensor_user -d sensor_data -c \
  "SELECT COUNT(*) FROM trv_temperatures;"
```

## Verifying the Full Integration

1. ✓ Service builds: `docker-compose build hubitat-agent`
2. ✓ Service starts: `balena logs hubitat-agent` shows no errors
3. ✓ Migrations run: `SELECT COUNT(*) FROM trv_temperatures;` works
4. ✓ Data inserted: Rows appear in the table after 60 seconds
5. ✓ Data queryable: Grafana can query the metrics

## Expected Log Output

When everything works:

```
INFO:hubitat_agent:Running migration: 001_create_trv_temperatures.sql
INFO:migrations:Running migration: 001_create_trv_temperatures.sql
INFO:migrations:All migrations completed successfully
INFO:hubitat_agent:Starting poll loop (interval=60s)
INFO:hubitat_agent:Inserted 3 device rows
INFO:hubitat_agent:Inserted 3 device rows
...
```

If you see `Inserted 0 device rows` repeatedly, the API is returning no TRV devices. Verify:
- API URL is correct
- Token is valid
- Hubitat hub has TRV devices configured
