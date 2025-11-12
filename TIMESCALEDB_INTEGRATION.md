# TimescaleDB Integration Summary

## Changes Made

### 1. **docker-compose.yml** - Updated
- Added TimescaleDB service with PostgreSQL 15
- Configured health checks for database readiness
- Added persistent volume for database data
- Updated temp-monitor service with database dependency
- Added DATABASE_URL environment variable

### 2. **docker-compose.dev.yml** - Updated
- Added TimescaleDB service (same as production)
- Uses separate dev volume for data isolation
- Same configuration as docker-compose.yml

### 3. **temp_monitor.py** - Enhanced
Added database integration:
- **`init_database()`** - Initializes database connection and creates hypertable schema
- **`store_sensor_data()`** - Stores sensor readings in TimescaleDB after each poll
- Updated **`main()`** - Now initializes database before starting monitoring loop
- Automatic table creation and indexing

### 4. **requirements.txt** - Updated
- Added `psycopg2-binary==2.9.9` for PostgreSQL connectivity

### 5. **TIMESCALEDB_SETUP.md** - Created
- Complete setup and usage guide
- Database schema documentation
- Sample SQL queries for data analysis
- Troubleshooting guide

## Key Features

✅ **Time-Series Optimized**: Uses TimescaleDB hypertables for efficient time-series storage  
✅ **Automatic Schema Creation**: Database table and indexes created on startup  
✅ **Data Persistence**: Named volumes ensure data survives container restarts  
✅ **Health Checks**: Database must be ready before app connects  
✅ **Flexible Configuration**: Environment variables for all settings  
✅ **Batch Insertion**: Efficient batch writes to database  
✅ **Indexed Queries**: Fast lookups by sensor_id and time  

## Quick Start

```bash
# Start both containers
docker-compose up

# View logs
docker-compose logs -f temp-monitor

# Query data
docker-compose exec timescaledb psql -U sensor_user -d sensor_data

# Stop
docker-compose down
```

## Database Access

- **Host**: `timescaledb` (or `localhost:5432` from host)
- **User**: `sensor_user`
- **Password**: `sensor_password`
- **Database**: `sensor_data`
- **Table**: `sensor_readings`

## Data Being Stored

For each sensor, the following is recorded:
- `time` - Timestamp of reading
- `sensor_id` - Sensor number (1-8)
- `temperature_celsius` - Temperature in Celsius
- `temperature_fahrenheit` - Temperature in Fahrenheit
- `raw_value` - Raw MODBUS value

## Next Steps

1. Start the containers: `docker-compose up`
2. Monitor the logs for successful database initialization
3. Query the data using the examples in TIMESCALEDB_SETUP.md
4. Consider adding retention policies and compression for long-term storage
5. Set up Grafana or similar visualization tool to display the data
