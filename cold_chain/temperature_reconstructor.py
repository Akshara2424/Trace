"""
temperature_reconstructor.py
----------------------------
Cold-chain temperature monitoring for vehicle routes: sparse sensor logging,
interpolation-based reconstruction, and excursion event detection.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Tuple, Dict


def generate_sparse_sensor_logs(
    route_coords: List[Tuple[float, float, datetime]],
    n_sensors: int = 5,
    duration_minutes: int = 60
) -> pd.DataFrame:
    """
    Generate sparse temperature sensor readings along a vehicle route.
    
    Args:
        route_coords: List of (lat, lon, timestamp) tuples representing vehicle path
        n_sensors: Number of temperature sensors in fleet
        duration_minutes: Total monitoring duration
        
    Returns:
        DataFrame with columns: [timestamp, lat, lon, temp_celsius, sensor_id]
    """
    rng = np.random.default_rng(42)
    
    # Extract timestamp and ensure it's a datetime object
    ts = route_coords[0][2]
    if isinstance(ts, (int, float)):
        # Convert Unix timestamp to datetime
        start_time = datetime.fromtimestamp(ts)
    else:
        # Already a datetime object
        start_time = ts
    
    records = []
    current_time = start_time
    
    while (current_time - start_time).total_seconds() / 60 < duration_minutes:
        if rng.random() > 0.3:  # 70% reading probability
            interval = int(rng.integers(8, 16))  # 8-15 minute intervals (convert to int)
            current_time += timedelta(minutes=interval)
            
            # Interpolate position at reading time
            elapsed = (current_time - start_time).total_seconds() / 60
            idx = min(int(elapsed * len(route_coords) / duration_minutes), len(route_coords) - 1)
            lat, lon, _ = route_coords[idx]
            
            # Temperature: base 8°C + Gaussian noise (σ=0.8)
            temp = 8.0 + rng.normal(0, 0.8)
            
            records.append({
                'timestamp': current_time,
                'lat': lat + rng.normal(0, 0.0001),
                'lon': lon + rng.normal(0, 0.0001),
                'temp_celsius': temp,
                'sensor_id': int(rng.integers(1, n_sensors + 1))
            })
    
    return pd.DataFrame(records)


def reconstruct_temperature_history(
    sparse_logs: pd.DataFrame,
    route_coords: List[Tuple[float, float, datetime]]
) -> pd.DataFrame:
    """
    Reconstruct dense temperature history via linear interpolation + Kalman-style smoothing.
    
    Args:
        sparse_logs: DataFrame with sparse sensor readings
        route_coords: List of (lat, lon, timestamp) route waypoints
        
    Returns:
        Dense DataFrame with reconstructed temperature at every route point
    """
    # Extract timestamp and ensure it's a datetime object
    ts = route_coords[0][2]
    if isinstance(ts, (int, float)):
        # Convert Unix timestamp to datetime
        start_time = datetime.fromtimestamp(ts)
    else:
        # Already a datetime object
        start_time = ts
    
    timestamps = [t if isinstance(t, datetime) else datetime.fromtimestamp(t) for _, _, t in route_coords]
    
    # Linear interpolation to dense grid
    time_sparse = [(t - start_time).total_seconds() for t in sparse_logs['timestamp']]
    time_dense = [(t - start_time).total_seconds() for t in timestamps]
    
    interp_temps = np.interp(time_dense, time_sparse, sparse_logs['temp_celsius'].values)
    
    # Kalman-style filtering: exponential moving average with α=0.3
    smoothed = np.zeros_like(interp_temps, dtype=float)
    smoothed[0] = interp_temps[0]
    alpha = 0.3
    
    for i in range(1, len(interp_temps)):
        smoothed[i] = alpha * interp_temps[i] + (1 - alpha) * smoothed[i - 1]
    
    records = []
    for (lat, lon, ts), temp in zip(route_coords, smoothed):
        records.append({'timestamp': ts, 'lat': lat, 'lon': lon, 'temp_celsius': temp})
    
    return pd.DataFrame(records)


def compute_time_above_threshold(
    reconstructed: pd.DataFrame,
    threshold_celsius: float = 8.0
) -> Dict:
    """
    Compute time-above-threshold statistics and identify excursion events.
    
    Args:
        reconstructed: Dense reconstructed temperature DataFrame
        threshold_celsius: Temperature threshold for excursion detection
        
    Returns:
        Dict with keys:
            - total_minutes_above: Total minutes above threshold
            - max_excursion_temp: Peak temperature during excursions
            - excursion_events: List of {start, end} timestamp pairs
    """
    above = reconstructed[reconstructed['temp_celsius'] > threshold_celsius].copy()
    
    if len(above) == 0:
        return {'total_minutes_above': 0, 'max_excursion_temp': 0, 'excursion_events': []}
    
    # Identify contiguous excursion events (gap > 5 min = new event)
    events = []
    excursion_start = above.iloc[0]['timestamp']
    prev_ts = excursion_start
    
    for idx, (_, row) in enumerate(above.iloc[1:].iterrows(), 1):
        gap = (row['timestamp'] - prev_ts).total_seconds()
        if gap > 300:  # 5-minute gap threshold
            events.append({'start': excursion_start, 'end': prev_ts})
            excursion_start = row['timestamp']
        prev_ts = row['timestamp']
    
    events.append({'start': excursion_start, 'end': prev_ts})
    
    # Total minutes = count × interval between samples
    sample_interval = (reconstructed['timestamp'].iloc[1] - 
                      reconstructed['timestamp'].iloc[0]).total_seconds() / 60
    total_minutes_above = len(above) * sample_interval
    
    return {
        'total_minutes_above': total_minutes_above,
        'max_excursion_temp': above['temp_celsius'].max(),
        'excursion_events': events
    }
