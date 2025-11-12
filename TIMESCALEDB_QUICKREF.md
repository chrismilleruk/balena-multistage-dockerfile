# Quick Reference: TimescaleDB + Sensor Monitor

## Directory Structure

```
.
├── docker-compose.yml              # Production setup
├── docker-compose.dev.yml          # Development setup
├── temp_monitor.py                 # Main app (now with DB support)
├── requirements.txt                # Python dependencies (added psycopg2)
├── Dockerfile.template             # Docker build config
├── TIMESCALEDB_SETUP.md           # Detailed setup guide
└── TIMESCALEDB_INTEGRATION.md     # Integration summary
```

## Environment Variables

Available for both containers:

```bash
# Sensor Configuration
SERIAL_PORT=/dev/ttyACM0           # Serial port for sensor
BAUDRATE=9600                      # Baud rate
MODBUS_ADDRESS=1                   # MODBUS device address
TIMEOUT=3                          # Timeout in seconds
POLL_INTERVAL=5                    # Read interval in seconds

# Database Configuration
DATABASE_URL=postgresql://sensor_user:sensor_password@timescaledb:5432/sensor_data
```

## Common Commands

### Start Services
```bash
# Production
docker-compose up -d

# Development
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose logs -f temp-monitor
```

### Database Access
```bash
# Connect to database
docker-compose exec timescaledb psql -U sensor_user -d sensor_data

# View data
psql> SELECT * FROM sensor_readings ORDER BY time DESC LIMIT 10;

# Exit
psql> \q
```

### Stop Services
```bash
# Stop and remove containers
docker-compose down

# Stop and remove everything including volumes
docker-compose down -v
```

## Database Schema

```
Table: sensor_readings (TimescaleDB Hypertable)
├── time (TIMESTAMPTZ) - Measurement timestamp
├── sensor_id (INTEGER) - Sensor number 1-8
├── temperature_celsius (DOUBLE) - Temperature in °C
├── temperature_fahrenheit (DOUBLE) - Temperature in °F
└── raw_value (INTEGER) - Raw MODBUS register value

Index: sensor_readings_sensor_id_time
└── (sensor_id, time DESC) - For fast time-series queries
```

## Data Flow

```
Sensor (MODBUS RTU)
        ↓ (Serial)
   temp_monitor.py
        ↓ (Read & Convert)
   store_sensor_data()
        ↓ (PostgreSQL)
   TimescaleDB Container
        ↓ (Network)
   Can query/visualize data
```

## Useful Queries

### Latest readings
```sql
SELECT * FROM sensor_readings 
WHERE time > NOW() - INTERVAL '1 hour'
ORDER BY time DESC LIMIT 20;
```

### Temperature statistics
```sql
SELECT sensor_id, 
       AVG(temperature_celsius) as avg_c,
       MIN(temperature_celsius) as min_c,
       MAX(temperature_celsius) as max_c,
       MAX(time) as last_read
FROM sensor_readings
WHERE time > NOW() - INTERVAL '24 hours'
GROUP BY sensor_id;
```

### Data volume check
```sql
SELECT 
    COUNT(*) as total_records,
    COUNT(DISTINCT sensor_id) as unique_sensors,
    MIN(time) as oldest,
    MAX(time) as newest
FROM sensor_readings;
```

## Monitoring

```bash
# Check container health
docker-compose ps

# View TimescaleDB logs
docker-compose logs timescaledb

# View temp-monitor logs
docker-compose logs temp-monitor

# Check volume status
docker volume ls | grep timescaledb
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Connection refused" | Wait for health check: `docker-compose ps` |
| No data writing | Check temp-monitor logs for sensor/DB errors |
| Disk space full | Check volume: `docker system df` or query `pg_database_size()` |
| Slow queries | Check index: `SELECT * FROM pg_indexes WHERE tablename='sensor_readings';` |

## Storage Management

### Enable data retention (30 days)
```sql
SELECT add_retention_policy('sensor_readings', INTERVAL '30 days');
```

### Enable compression (7+ days old)
```sql
SELECT add_compression_policy('sensor_readings', INTERVAL '7 days');
```

### Check policy status
```sql
SELECT * FROM timescaledb_information.jobs;
```

## Performance Tips

1. **Retention**: Clean old data to save space
2. **Compression**: Compress data older than 7 days
3. **Queries**: Use time ranges for faster results
4. **Indexes**: The app creates necessary indexes automatically
5. **Aggregates**: Use `time_bucket()` for efficient time-series aggregation

## Files Modified

- ✅ `docker-compose.yml` - Added TimescaleDB service
- ✅ `docker-compose.dev.yml` - Added TimescaleDB service
- ✅ `temp_monitor.py` - Added database integration
- ✅ `requirements.txt` - Added psycopg2-binary
- ✅ `TIMESCALEDB_SETUP.md` - Created (detailed guide)
- ✅ `TIMESCALEDB_INTEGRATION.md` - Created (summary)
