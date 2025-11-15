-- Create table for TRV temperature time-series
CREATE TABLE IF NOT EXISTS trv_temperatures (
    time timestamptz NOT NULL,
    device_id text NOT NULL,
    label text,
    room text,
    temperature double precision,
    setpoint double precision,
    battery integer,
    health_status text,
    operating_state text,
    raw jsonb
);

-- Make hypertable (TimescaleDB)
SELECT create_hypertable('trv_temperatures', 'time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS trv_temperatures_device_time_idx ON trv_temperatures (device_id, time DESC);
