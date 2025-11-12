# TimescaleDB Sensor Data Plotting

Python scripts for connecting to the TimescaleDB container and visualizing sensor readings.

## Database Schema

The `sensor_readings` table contains:
- `time` - timestamp with timezone
- `sensor_id` - integer sensor identifier
- `temperature_celsius` - temperature in Celsius
- `temperature_fahrenheit` - temperature in Fahrenheit
- `raw_value` - raw ADC reading

## Setup

1. Ensure TimescaleDB container is running:
```bash
balena push <device-ip> --local
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Quick Start

Run the script to generate all plots:
```bash
python plot_data.py
```

This will create:
- `temperature_timeseries.png` - Temperature trends over time for all sensors
- `sensor_comparison.png` - Average temperature by sensor with min/max ranges
- `raw_values_distribution.png` - Distribution of raw sensor values

### Custom Plotting

```python
from plot_data import SensorDataPlotter
import matplotlib.pyplot as plt

# Connect to TimescaleDB
plotter = SensorDataPlotter(
    host="localhost",
    port=5432,
    database="sensor_data",
    user="sensor_user",
    password="sensor_password"
)
plotter.connect()

# Plot specific sensors
fig = plotter.plot_temperature_time_series(
    sensor_ids=[1, 2, 3],
    hours=12,
    use_fahrenheit=False
)
plt.savefig("my_plot.png")
plt.show()

# Get raw data for custom analysis
df = plotter.get_sensor_data(sensor_ids=[1], hours=6)
print(df.describe())

plotter.disconnect()
```

## Available Methods

- `get_sensor_data(sensor_ids, hours)` - Fetch sensor data as pandas DataFrame
- `plot_temperature_time_series(sensor_ids, hours, use_fahrenheit)` - Time series plot
- `plot_sensor_comparison(hours)` - Bar chart comparing sensor statistics
- `plot_raw_values_distribution(sensor_ids, hours)` - Histogram of raw values

## Connection Details

The TimescaleDB service is defined in `../docker-compose.yml`:
- **Host**: localhost (when accessing from host machine)
- **Port**: 5432
- **Database**: sensor_data
- **User**: sensor_user
- **Password**: sensor_password
