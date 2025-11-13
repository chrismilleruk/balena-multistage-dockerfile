#!/usr/bin/env python3
"""
calibrate.py

Compute calibration offsets from recent sensor readings and apply them to the sensors table.

Supports two methods:
1. --method median: Use per-timestamp median of all sensors as reference
2. --method reference: Use a specific sensor (--ref-id) as the reference

Usage:
  # Median consensus over last 15 minutes
  DATABASE_URL=postgresql://... python3 calibrate.py --method median --minutes 15

  # Use sensor id 1 as reference
  DATABASE_URL=postgresql://... python3 calibrate.py --method reference --ref-id 1 --minutes 10

Environment:
  DATABASE_URL: PostgreSQL connection string (required)
"""

import os
import sys
import argparse
import psycopg2
from datetime import datetime, timedelta
import statistics


def fetch_recent_readings(conn, minutes=10):
    """Fetch recent sensor readings (raw values) grouped by sensor_id."""
    cursor = conn.cursor()
    since = datetime.utcnow() - timedelta(minutes=minutes)
    cursor.execute("""
        SELECT sensor_id, time, raw_value
        FROM sensor_readings
        WHERE time >= %s
        ORDER BY time ASC
    """, (since,))
    rows = cursor.fetchall()
    cursor.close()
    
    # Group by sensor_id
    data = {}
    for sensor_id, ts, raw in rows:
        data.setdefault(sensor_id, []).append((ts, raw))
    return data


def compute_offsets_median(data):
    """
    Compute offsets using median consensus.
    
    Strategy: compute per-sensor mean raw value over the collection period,
    use the median of all means as reference, then offsets = reference - sensor_mean.
    Offsets are returned as raw units (integers, 0.1°C).
    """
    means = {}
    for sid, samples in data.items():
        raws = [r for _, r in samples]
        if raws:
            means[sid] = sum(raws) / len(raws)
    
    if not means:
        return {}
    
    median_of_means = statistics.median(list(means.values()))
    # Offsets in raw units (0.1°C); round to nearest integer
    offsets = {sid: int(round(median_of_means - m)) for sid, m in means.items()}
    return offsets


def compute_offsets_reference(data, ref_id):
    """
    Compute offsets using a specific reference sensor.
    
    Strategy: use the mean raw value of the reference sensor,
    compute offset for all others as (ref_mean - sensor_mean).
    Offsets are returned as raw units (integers, 0.1°C).
    """
    if ref_id not in data or not data[ref_id]:
        raise ValueError(f"Reference sensor {ref_id} has no recent samples")
    
    ref_samples = data[ref_id]
    ref_mean = sum([r for _, r in ref_samples]) / len(ref_samples)
    
    offsets = {}
    for sid, samples in data.items():
        if not samples:
            continue
        mean = sum([r for _, r in samples]) / len(samples)
        # Offset in raw units; round to nearest integer
        offsets[sid] = int(round(ref_mean - mean))
    
    return offsets


def apply_offsets(conn, offsets):
    """Write computed offsets to sensors.calibration_offset."""
    cursor = conn.cursor()
    for sid, offset in offsets.items():
        cursor.execute(
            "UPDATE sensors SET calibration_offset = %s WHERE id = %s",
            (float(offset), int(sid))
        )
    conn.commit()
    cursor.close()


def main():
    parser = argparse.ArgumentParser(
        description="Compute and apply calibration offsets from recent sensor readings"
    )
    parser.add_argument(
        "--method",
        choices=("median", "reference"),
        default="median",
        help="Calibration method: median consensus or reference sensor"
    )
    parser.add_argument(
        "--minutes",
        type=int,
        default=10,
        help="Time window (minutes) for recent readings"
    )
    parser.add_argument(
        "--ref-id",
        type=int,
        help="Sensor id to use as reference (required for --method reference)"
    )
    args = parser.parse_args()

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)

    try:
        conn = psycopg2.connect(database_url)
    except Exception as e:
        print(f"ERROR: Failed to connect to database: {e}")
        sys.exit(1)

    try:
        data = fetch_recent_readings(conn, minutes=args.minutes)
        if not data:
            print("No recent readings found in the database")
            return

        print(f"Found {sum(len(s) for s in data.values())} readings across {len(data)} sensors in the last {args.minutes} minutes\n")

        if args.method == "median":
            print("Computing offsets using median consensus method...")
            offsets = compute_offsets_median(data)
        else:
            if not args.ref_id:
                print("ERROR: --ref-id required for reference method")
                sys.exit(1)
            print(f"Computing offsets using sensor {args.ref_id} as reference...")
            offsets = compute_offsets_reference(data, args.ref_id)

        if not offsets:
            print("No offsets computed")
            return

        print("\nComputed offsets (sensor_id: raw_offset in 0.1°C units):")
        for sid in sorted(offsets.keys()):
            off = offsets[sid]
            print(f"  Sensor {sid:2d}: {int(off):+3d}")

        print("\nApplying offsets to database...")
        apply_offsets(conn, offsets)
        print("Done.")

    finally:
        conn.close()


if __name__ == '__main__':
    main()
