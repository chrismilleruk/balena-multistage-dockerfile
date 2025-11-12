# TimescaleDB Integration Guide

This project now includes TimescaleDB for time-series sensor data storage.

## Architecture

The solution consists of two containers:
- **timescaledb**: PostgreSQL with TimescaleDB extension for efficient time-series data storage
- **temp-monitor**: Python application that reads sensors and stores data in TimescaleDB

## Database Schema

The `sensor_readings` table stores temperature data with the following structure:

```sql
CREATE TABLE sensor_readings (
    time TIMESTAMPTZ NOT NULL,
    sensor_id INTEGER NOT NULL,
    temperature_celsius DOUBLE PRECISION NOT NULL,
    temperature_fahrenheit DOUBLE PRECISION NOT NULL,
    raw_value INTEGER
);
```

This table is automatically created as a **hypertable**, which provides:
- Automatic partitioning by time for better performance
- Compression for older data
- Efficient queries on time-series data

## Connection Details

**Database Credentials:**
- Username: `sensor_user`
- Password: `sensor_password`
- Database: `sensor_data`
- Connection string: `postgresql://sensor_user:sensor_password@timescaledb:5432/sensor_data`

## Deployment

### Using Docker Compose

```bash
docker-compose up
```

This will:
1. Start the TimescaleDB container with data persistence
2. Start the temp-monitor service
3. Automatically initialize the database schema

### Environment Variables

You can customize the connection by setting `DATABASE_URL`:

```bash
docker-compose -e DATABASE_URL="postgresql://user:password@host:5432/db" up
```

## Querying the Data

### Connect to the database

```bash
docker-compose exec timescaledb psql -U sensor_user -d sensor_data
```

### Sample Queries

**Get latest readings for all sensors:**
```sql
SELECT * FROM sensor_readings 
WHERE time > NOW() - INTERVAL '1 hour'
ORDER BY time DESC, sensor_id;
```

**Get average temperature per sensor (last 24 hours):**
```sql
SELECT 
    sensor_id,
    AVG(temperature_celsius) as avg_temp_c,
    MIN(temperature_celsius) as min_temp_c,
    MAX(temperature_celsius) as max_temp_c
FROM sensor_readings
WHERE time > NOW() - INTERVAL '24 hours'
GROUP BY sensor_id;
```

**Enable compression on old data:**
```sql
SELECT add_compression_policy('sensor_readings', INTERVAL '7 days');
```

**View continuous aggregates (if needed):**
```sql
CREATE MATERIALIZED VIEW sensor_hourly_avg AS
SELECT 
    time_bucket('1 hour', time) as hour,
    sensor_id,
    AVG(temperature_celsius) as avg_temp_c,
    MAX(temperature_celsius) as max_temp_c,
    MIN(temperature_celsius) as min_temp_c
FROM sensor_readings
GROUP BY hour, sensor_id;
```

## Data Persistence

The database uses a named volume `timescaledb_data` that persists data between container restarts.

To clean up the volume:
```bash
docker-compose down -v
```

## Monitoring

Check the monitoring logs:
```bash
docker-compose logs -f temp-monitor
```

The app logs:
- Database initialization status
- Number of records stored with each read cycle
- Connection errors and issues

## Performance Considerations

1. **Retention Policy**: Consider implementing data retention to manage storage:
```sql
SELECT add_retention_policy('sensor_readings', INTERVAL '30 days');
```

2. **Compression**: Enable automatic compression for data older than 7 days to save space
3. **Indexes**: The app creates an index on (sensor_id, time) for fast lookups

## Troubleshooting

**Connection refused error:**
- Ensure timescaledb container is healthy: `docker-compose ps`
- Check logs: `docker-compose logs timescaledb`
- Wait for health check to pass before temp-monitor connects

**Database initialization fails:**
- Check database credentials in docker-compose.yml
- Verify DATABASE_URL environment variable
- Check PostgreSQL logs: `docker-compose logs timescaledb`

**No data being written:**
- Verify sensor reading is working (check display output)
- Check temp-monitor logs for database errors
- Verify network connectivity between containers
