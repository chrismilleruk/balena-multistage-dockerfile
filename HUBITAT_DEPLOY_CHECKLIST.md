# 🚀 Hubitat Agent - Deployment Checklist

## Pre-Deployment Verification

- [ ] All files are in place (checked below)
- [ ] Docker-compose files have correct build context and Dockerfile path
- [ ] Dockerfile copies migrations directory
- [ ] migrations.py correctly points to ../migrations
- [ ] main.py calls run_migrations() before starting agent
- [ ] requirements-hubitat.txt has all dependencies (requests, psycopg2, Flask)

### File Inventory

```bash
# Verify these files exist:
ls -lh hubitat_agent/{main.py,hubitat_client.py,db.py,migrations.py,Dockerfile,requirements-hubitat.txt}
ls -lh migrations/001_create_trv_temperatures.sql
grep -q "hubitat-agent:" docker-compose.yml && echo "✓ docker-compose.yml configured"
grep -q "context: ." docker-compose.yml && echo "✓ build context is project root"
grep -q "dockerfile: hubitat_agent/Dockerfile" docker-compose.yml && echo "✓ Dockerfile path correct"
```

## Pre-Push Testing (Optional but Recommended)

```bash
# 1. Build image locally
docker-compose build hubitat-agent

# 2. Check Dockerfile syntax
docker build --no-cache -f hubitat_agent/Dockerfile .

# 3. Syntax check Python files
python -m py_compile hubitat_agent/main.py
python -m py_compile hubitat_agent/hubitat_client.py
python -m py_compile hubitat_agent/db.py
python -m py_compile hubitat_agent/migrations.py
```

## Deployment to Balena Device

### 1. Push Code
```bash
# From project directory
balena push c45f46e.local
```

**What happens:**
- Balena pulls latest code
- Builds `hubitat-agent` image using Dockerfile
- Copies `hubitat_agent/` and `migrations/` into container
- Starts service and runs migrations automatically

### 2. Set Environment Variables

**Option A: Via Balena Cloud UI (Recommended)**
1. Navigate to device in balena Cloud
2. Click "Environment variables"
3. Add:
   - `HUBITAT_API_URL` = `http://192.168.10.109/apps/api/50/devices/all?access_token=YOUR_TOKEN_HERE`
   - `MODE` = `poll`
   - `POLL_INTERVAL_SECONDS` = `60`

**Option B: Via SSH**
```bash
balena ssh c45f46e.local

# Inside device shell:
export HUBITAT_API_URL="http://192.168.10.109/apps/api/50/devices/all?access_token=YOUR_TOKEN"
export MODE="poll"
export POLL_INTERVAL_SECONDS=60

# Then restart service
balena restart hubitat-agent
```

### 3. Wait for Service to Start

The first startup will:
- Run migrations (~5-10 seconds)
- Create `trv_temperatures` table
- Start polling loop

```bash
# Watch startup
balena logs c45f46e.local -f hubitat-agent

# Expected output:
# INFO:hubitat_agent:Running migration: 001_create_trv_temperatures.sql
# INFO:migrations:All migrations completed successfully
# INFO:hubitat_agent:Starting poll loop (interval=60s)
```

### 4. Verify Data

After ~60 seconds, check that data is being inserted:

```bash
# Option A: Query from host
docker-compose exec timescaledb psql -U sensor_user -d sensor_data -c \
  "SELECT COUNT(*) FROM trv_temperatures;"

# Option B: Query from device via SSH
balena ssh c45f46e.local
balena exec timescaledb psql -U sensor_user -d sensor_data -c \
  "SELECT COUNT(*) FROM trv_temperatures;"

# Option C: See actual data
balena exec timescaledb psql -U sensor_user -d sensor_data <<EOF
SELECT device_id, label, room, temperature, setpoint, battery, operating_state, time
FROM trv_temperatures
ORDER BY time DESC
LIMIT 10;
EOF
```

## Monitoring & Diagnostics

### Check Service Status
```bash
balena ls c45f46e.local  # See all services
```

### View Logs
```bash
# Real-time logs
balena logs c45f46e.local -f hubitat-agent

# Last 100 lines
balena logs c45f46e.local hubitat-agent -n 100

# Errors only
balena logs c45f46e.local hubitat-agent | grep -i error
```

### Test API Connectivity
```bash
balena ssh c45f46e.local

# From inside device:
curl "http://192.168.10.109/apps/api/50/devices/all?access_token=YOUR_TOKEN"

# Should return JSON array of devices
```

### Test Database Connectivity
```bash
balena ssh c45f46e.local

# From inside device:
balena exec hubitat-agent bash
psql postgresql://sensor_user:sensor_password@timescaledb:5432/sensor_data -c "SELECT 1;"

# Should return: 1
```

### Run One-Time Fetch (For Testing)
```bash
balena ssh c45f46e.local

# From inside device:
balena exec hubitat-agent bash -c "RUN_ONCE=true python main.py"

# Check logs for errors
balena logs c45f46e.local -f hubitat-agent
```

## Troubleshooting

| Symptom | Cause | Solution |
|---------|-------|----------|
| Service won't start | Missing env vars | Set `HUBITAT_API_URL` in environment |
| "HUBITAT_API_URL or HUBITAT_HOST+HUBITAT_TOKEN must be provided" | Env vars not set | Set in balena Cloud UI or device shell |
| Migration errors in logs | Bad SQL or DB issues | Check `trv_temperatures` table exists; verify TimescaleDB is running |
| "Failed to fetch devices" | API unreachable | Test curl from device; verify token valid; check network |
| "connection refused" to timescaledb | DB not running | `balena ls c45f46e.local` should show timescaledb running |
| "Inserted 0 device rows" repeatedly | No TRV devices in Hubitat | Verify TRV devices exist in Hubitat; check API response with curl |

## Success Criteria

✅ **Service is working when you see:**

1. Logs show: `All migrations completed successfully`
2. Logs show: `Inserted X device rows` (X > 0)
3. `SELECT COUNT(*) FROM trv_temperatures;` returns > 0
4. `SELECT * FROM trv_temperatures;` shows recent rows with your device data

## Rollback

If something goes wrong:

```bash
# Stop the service
balena restart hubitat-agent

# Or remove and restart the entire stack
balena push c45f46e.local  # Will rebuild and restart all services

# Or SSH and manually restart
balena ssh c45f46e.local
balena stop hubitat-agent
balena start hubitat-agent
```

## Configuration Reference

| Variable | Default | Options | Description |
|----------|---------|---------|-------------|
| `HUBITAT_API_URL` | (empty) | full URL | Complete API endpoint with token |
| `HUBITAT_HOST` | (empty) | IP or hostname | Hubitat host (use with TOKEN) |
| `HUBITAT_TOKEN` | (empty) | access token | Maker API token (use with HOST) |
| `TIMESCALEDB_URL` | `postgresql://sensor_user:sensor_password@timescaledb:5432/sensor_data` | connection string | Database connection |
| `MODE` | `poll` | `poll`, `server` | Operating mode |
| `POLL_INTERVAL_SECONDS` | `60` | integer | Polling interval in seconds |
| `RUN_ONCE` | `false` | `true`, `false` | Run once and exit (for testing) |
| `HOST` | `0.0.0.0` | IP address | Server bind address (server mode) |
| `PORT` | `8080` | integer | Server port (server mode) |

## Next Steps After Deployment

1. ✅ Verify data in `trv_temperatures` table
2. ➜ Create Grafana dashboard querying the data
3. ➜ Add alerts for battery low or device offline
4. ➜ Consider scaling: add more TRV devices, reduce poll interval
5. ➜ Document room layout / device mapping in project wiki

---

**Ready to deploy!** Run `balena push c45f46e.local` 🚀
