"""
ambient_overlay.py
------------------
Urban heat island modeling and historical ambient temperature fetching.
Integrates traffic density heatmap with thermal penalties and Open-Meteo API.
"""

import requests
from datetime import datetime
from typing import List, Dict, Tuple


def traffic_density_to_thermal_penalty(
    heatmap_data: List[List[float]],
    base_temp: float = 25.0
) -> List[List[float]]:
    """
    Map traffic density to urban heat island thermal penalty.
    
    Args:
        heatmap_data: List of [lat, lon, weight] where weight ∈ [0, 1]
        base_temp: Base ambient temperature in Celsius
        
    Returns:
        Augmented list: [lat, lon, weight, ambient_temp_celsius]
        thermal_penalty = weight * 3.5°C (0 at density=0, +3.5°C at density=1)
    """
    augmented = []
    for lat, lon, weight in heatmap_data:
        # Linear UHI penalty: 0°C @ weight=0, 3.5°C @ weight=1
        thermal_penalty = weight * 3.5
        ambient_temp = base_temp + thermal_penalty
        augmented.append([lat, lon, weight, ambient_temp])
    
    return augmented


def fetch_ambient_temperature(lat: float, lon: float, timestamp: str) -> float:
    """
    Fetch historical ambient temperature from Open-Meteo API.
    
    Args:
        lat: Latitude (WGS84)
        lon: Longitude (WGS84)
        timestamp: ISO 8601 timestamp string (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
        
    Returns:
        Hourly temperature in Celsius, or 28.0°C (seasonal average) if API fails
    """
    try:
        # Parse timestamp to extract date and hour
        if 'T' in timestamp:
            dt = datetime.fromisoformat(timestamp)
        else:
            dt = datetime.fromisoformat(timestamp)
        
        start_date = dt.strftime('%Y-%m-%d')
        hour = dt.hour if 'T' in timestamp else 12  # Default to noon if no time given
        
        # Open-Meteo historical API endpoint
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            'latitude': lat,
            'longitude': lon,
            'start_date': start_date,
            'end_date': start_date,
            'hourly': 'temperature_2m',
            'timezone': 'auto'
        }
        
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        if 'hourly' in data and 'temperature_2m' in data['hourly']:
            temps = data['hourly']['temperature_2m']
            # Clamp hour to valid range [0, 23]
            hour = min(hour, len(temps) - 1)
            return float(temps[hour])
        
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
    except (KeyError, IndexError, ValueError) as e:
        print(f"Data parsing error: {e}")
    
    # Fallback: Indian seasonal average (summer ~28°C, winter ~20°C, monsoon ~26°C)
    # Heuristic: if month in [3-5], use 32°C (peak summer), else 26°C
    try:
        month = datetime.fromisoformat(timestamp if 'T' in timestamp else timestamp).month
        return 32.0 if month in [3, 4, 5] else 26.0
    except:
        return 28.0


if __name__ == '__main__':
    # Test block
    print("=" * 60)
    print("Testing ambient_overlay.py")
    print("=" * 60)
    
    # Test 1: Traffic density to thermal penalty
    print("\n[Test 1] Traffic Density → Thermal Penalty")
    heatmap = [
        [28.6315, 77.2167, 0.0],    # No traffic
        [28.6315, 77.2167, 0.5],    # Medium traffic
        [28.6315, 77.2167, 1.0],    # Heavy traffic
    ]
    augmented = traffic_density_to_thermal_penalty(heatmap, base_temp=25.0)
    for row in augmented:
        print(f"  Density weight={row[2]:.1f} → Ambient temp={row[3]:.1f}°C")
    
    # Test 2: Open-Meteo API call (historical data)
    print("\n[Test 2] Open-Meteo Historical Temperature Fetch")
    # Delhi, 2024-06-15, 14:00 UTC (peak summer day)
    lat, lon = 28.6315, 77.2167
    timestamp = "2024-06-15T14:00:00"
    
    try:
        temp = fetch_ambient_temperature(lat, lon, timestamp)
        print(f"  Location: ({lat}, {lon})")
        print(f"  Timestamp: {timestamp}")
        print(f"  Fetched temperature: {temp}°C")
    except Exception as e:
        print(f"  Error: {e}")
    
    print("\n[Test 3] Fallback (invalid date)")
    temp_fallback = fetch_ambient_temperature(28.6315, 77.2167, "invalid")
    print(f"  Fallback temperature: {temp_fallback}°C")
    
    print("\n" + "=" * 60)
