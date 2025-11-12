#!/usr/bin/env python3
"""
TimescaleDB sensor data plotting script
"""
import psycopg2
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List


class SensorDataPlotter:
    def __init__(self, host: str = "localhost", port: int = 5432,
                 database: str = "sensor_data", user: str = "sensor_user",
                 password: str = "sensor_password"):
        """Initialize TimescaleDB connection parameters"""
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.conn = None
    
    def connect(self):
        """Connect to TimescaleDB"""
        self.conn = psycopg2.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password
        )
        print(f"Connected to TimescaleDB: {self.database}@{self.host}")
    
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("Database connection closed")
    
    def query_to_dataframe(self, query: str) -> pd.DataFrame:
        """Execute query and return results as DataFrame"""
        if not self.conn:
            raise Exception("Not connected to database")
        df = pd.read_sql_query(query, self.conn)
        # Convert time column to datetime if present
        if 'time' in df.columns:
            df['time'] = pd.to_datetime(df['time'])
        return df
    
    def get_sensor_data(self, sensor_ids: Optional[List[int]] = None,
                       hours: int = 24) -> pd.DataFrame:
        """Get recent sensor data for specified sensors"""
        where_clause = ""
        if sensor_ids:
            sensor_list = ','.join(map(str, sensor_ids))
            where_clause = f"AND sensor_id IN ({sensor_list})"
        
        query = f"""
            SELECT time, sensor_id, temperature_celsius, temperature_fahrenheit, raw_value
            FROM sensor_readings
            WHERE time > NOW() - INTERVAL '{hours} hours'
            {where_clause}
            ORDER BY time, sensor_id
        """
        return self.query_to_dataframe(query)
    
    def plot_temperature_time_series(self, sensor_ids: Optional[List[int]] = None,
                                    hours: int = 24, use_fahrenheit: bool = False):
        """Plot temperature over time for specified sensors"""
        df = self.get_sensor_data(sensor_ids, hours)
        
        temp_col = 'temperature_fahrenheit' if use_fahrenheit else 'temperature_celsius'
        temp_unit = '°F' if use_fahrenheit else '°C'
        
        fig, ax = plt.subplots(figsize=(14, 7))
        
        for sensor_id in df['sensor_id'].unique():
            sensor_df = df[df['sensor_id'] == sensor_id]
            ax.plot(sensor_df['time'], sensor_df[temp_col], 
                   marker='o', label=f'Sensor {sensor_id}', alpha=0.7)
        
        ax.set_xlabel('Time')
        ax.set_ylabel(f'Temperature ({temp_unit})')
        ax.set_title(f'Temperature Readings - Last {hours} Hours')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Format x-axis dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        return fig
    
    def plot_sensor_comparison(self, hours: int = 24):
        """Plot average temperature by sensor"""
        query = f"""
            SELECT sensor_id, 
                   AVG(temperature_celsius) as avg_temp_c,
                   MIN(temperature_celsius) as min_temp_c,
                   MAX(temperature_celsius) as max_temp_c,
                   COUNT(*) as reading_count
            FROM sensor_readings
            WHERE time > NOW() - INTERVAL '{hours} hours'
            GROUP BY sensor_id
            ORDER BY sensor_id
        """
        df = self.query_to_dataframe(query)
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        x = df['sensor_id']
        ax.bar(x, df['avg_temp_c'], yerr=[df['avg_temp_c'] - df['min_temp_c'],
                                           df['max_temp_c'] - df['avg_temp_c']],
               capsize=5, alpha=0.7, edgecolor='black')
        
        ax.set_xlabel('Sensor ID')
        ax.set_ylabel('Temperature (°C)')
        ax.set_title(f'Temperature Statistics by Sensor - Last {hours} Hours')
        ax.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        return fig
    
    def plot_raw_values_distribution(self, sensor_ids: Optional[List[int]] = None,
                                    hours: int = 24):
        """Plot distribution of raw sensor values"""
        df = self.get_sensor_data(sensor_ids, hours)
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        for sensor_id in df['sensor_id'].unique():
            sensor_df = df[df['sensor_id'] == sensor_id]
            ax.hist(sensor_df['raw_value'], bins=20, alpha=0.5, 
                   label=f'Sensor {sensor_id}', edgecolor='black')
        
        ax.set_xlabel('Raw Value')
        ax.set_ylabel('Frequency')
        ax.set_title(f'Raw Value Distribution - Last {hours} Hours')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        return fig


def main():
    """Example usage - plot sensor data from TimescaleDB"""
    # Connect to TimescaleDB (using default connection from docker-compose)
    plotter = SensorDataPlotter(
        host="c45f46e.local",
        port=5432,
        database="sensor_data",
        user="sensor_user",
        password="sensor_password"
    )
    
    plotter.connect()
    
    try:
        # Get recent data
        print("Fetching sensor data...")
        df = plotter.get_sensor_data(hours=24)
        print(f"\nFound {len(df)} readings")
        print(f"Sensors: {sorted(df['sensor_id'].unique())}")
        print(f"\nLatest readings:")
        print(df.tail(10))
        
        # Create plots
        print("\nGenerating plots...")
        
        # Temperature time series
        fig1 = plotter.plot_temperature_time_series(hours=24)
        fig1.savefig('temperature_timeseries.png', dpi=150)
        print("Saved: temperature_timeseries.png")
        
        # Sensor comparison
        fig2 = plotter.plot_sensor_comparison(hours=24)
        fig2.savefig('sensor_comparison.png', dpi=150)
        print("Saved: sensor_comparison.png")
        
        # Raw values distribution
        fig3 = plotter.plot_raw_values_distribution(hours=24)
        fig3.savefig('raw_values_distribution.png', dpi=150)
        print("Saved: raw_values_distribution.png")
        
        print("\nDone! Use plt.show() to display plots.")
        # plt.show()  # Uncomment to display plots interactively
        
    finally:
        plotter.disconnect()


if __name__ == "__main__":
    main()
