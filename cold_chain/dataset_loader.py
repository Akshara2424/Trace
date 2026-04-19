"""
Dataset Loader for Cold Chain Simulations
Loads real Kaggle datasets (Delhi Traffic + Delivery Logistics) for realistic simulations
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, List, Optional
from datetime import datetime, timedelta


def load_delivery_logistics_sample(
    filepath: str = "datasets/Delivery_Logistics.csv",
    sample_size: int = 10
) -> Optional[pd.DataFrame]:
    """
    Load sample deliveries from Kaggle Delivery Logistics Dataset (India – Multi-Partner).
    
    Args:
        filepath: Path to Delivery_Logistics.csv
        sample_size: Number of delivery records to sample
    
    Returns:
        DataFrame with columns: [delivery_id, distance_km, delivery_time_min, 
                                 expected_time_min, weather, vehicle_type, weight_kg]
        Returns None if file not found
    """
    try:
        df = pd.read_csv(filepath)
        
        # Expected columns from Delivery Logistics Dataset
        required_cols = ['distance_km', 'delivery_time', 'expected_time', 'weather', 'vehicle_type', 'package_weight']
        
        # Rename columns if they exist with slight variations
        col_mapping = {
            'Delivery ID': 'delivery_id',
            'Distance': 'distance_km',
            'Delivery Time': 'delivery_time_min',
            'Expected Time': 'expected_time_min',
            'Weather Condition': 'weather',
            'Vehicle Type': 'vehicle_type',
            'Package Weight': 'weight_kg',
        }
        df.rename(columns=col_mapping, inplace=True)
        
        # Sample random deliveries
        sample = df.sample(n=min(sample_size, len(df)), random_state=42)
        return sample.reset_index(drop=True)
        
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error loading delivery logistics: {e}")
        return None


def load_delhi_traffic_sample(
    features_path: str = "datasets/delhi_traffic_features.csv",
    target_path: str = "datasets/delhi_traffic_target.csv",
    sample_size: int = 10
) -> Optional[pd.DataFrame]:
    """
    Load sample trips from Kaggle Delhi Traffic Travel Time Dataset.
    
    Args:
        features_path: Path to delhi_traffic_features.csv
        target_path: Path to delhi_traffic_target.csv
        sample_size: Number of trips to sample
    
    Returns:
        DataFrame with columns: [trip_id, distance_km, traffic_density, 
                                 weather, time_of_day, travel_time_min]
        Returns None if files not found
    """
    try:
        features_df = pd.read_csv(features_path)
        target_df = pd.read_csv(target_path)
        
        # Normalize column names first
        features_df.columns = features_df.columns.str.lower().str.replace(' ', '_')
        target_df.columns = target_df.columns.str.lower().str.replace(' ', '_')
        
        # Merge features with target on trip_id
        merged = features_df.merge(target_df, on='trip_id', how='inner')
        
        # Sample random trips
        sample = merged.sample(n=min(sample_size, len(merged)), random_state=42)
        return sample.reset_index(drop=True)
        
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error loading Delhi traffic: {e}")
        return None


def extract_route_from_delivery(delivery_record: Dict) -> List[Tuple[float, float, datetime]]:
    """
    Generate a route with lat/lon coordinates from a delivery record.
    Uses Delhi city bounds (28.4089°N - 28.8860°N, 76.8581°E - 77.3910°E)
    
    Args:
        delivery_record: Row from delivery dataset
    
    Returns:
        List of tuples: [(lat, lon, timestamp), ...]
    """
    # Delhi bounds
    lat_min, lat_max = 28.4089, 28.8860
    lon_min, lon_max = 76.8581, 77.3910
    
    distance_km = delivery_record.get('distance_km', 10)
    
    # Generate waypoints along a random path
    num_waypoints = max(5, int(distance_km / 2))
    route = []
    
    # Create a start datetime and increment it for each waypoint
    start_time = datetime.now()
    
    for i in range(num_waypoints):
        lat = lat_min + (lat_max - lat_min) * np.random.random()
        lon = lon_min + (lon_max - lon_min) * np.random.random()
        time_elapsed_minutes = int((i / num_waypoints) * distance_km * 3)  # ~3 min per km transit time
        timestamp = start_time + timedelta(minutes=time_elapsed_minutes)
        route.append((lat, lon, timestamp))
    
    return route


def extract_delay_from_traffic(traffic_record: Dict) -> float:
    """
    Extract realistic delay in minutes from Delhi traffic record.
    
    Args:
        traffic_record: Row from Delhi Traffic dataset
    
    Returns:
        Delay in minutes (positive = additional time vs baseline)
    """
    travel_time = traffic_record.get('travel_time_min', 20)
    expected_time = traffic_record.get('expected_time_min', 15)
    
    # Calculate delay
    delay = max(0, travel_time - expected_time)
    return delay


def extract_weather_from_delivery(delivery_record: Dict) -> str:
    """
    Extract weather condition from delivery record.
    
    Args:
        delivery_record: Row from delivery dataset
    
    Returns:
        Weather condition string (Clear, Rain, Fog, etc.)
    """
    weather = delivery_record.get('weather', 'Clear')
    return str(weather).strip()


def weather_to_thermal_penalty(weather: str) -> float:
    """
    Map weather condition to thermal penalty multiplier.
    Affects ambient temperature rise.
    
    Args:
        weather: Weather condition string
    
    Returns:
        Thermal penalty multiplier (0.8 to 1.5)
    """
    weather_lower = weather.lower()
    
    if 'rain' in weather_lower:
        return 0.85  # Rain = cooler ambient
    elif 'fog' in weather_lower:
        return 0.90  # Fog = slightly cooler
    elif 'clear' in weather_lower or 'sunny' in weather_lower:
        return 1.3  # Sunny = hotter ambient
    elif 'cloud' in weather_lower:
        return 1.0  # Cloudy = baseline
    else:
        return 1.0  # Default


def create_realistic_route(
    delivery_df: Optional[pd.DataFrame] = None,
    traffic_df: Optional[pd.DataFrame] = None
) -> Dict:
    """
    Create a realistic cold chain route by combining delivery + traffic data.
    
    Args:
        delivery_df: Sample from Delivery Logistics dataset
        traffic_df: Sample from Delhi Traffic dataset
    
    Returns:
        Dict with keys: {
            'route_coords': List of (lat, lon, time_min),
            'delivery_distance_km': float,
            'standard_delay_minutes': float,
            'weather': str,
            'vehicle_type': str,
            'package_weight_kg': float,
            'thermal_penalty': float
        }
    """
    route_data = {}
    
    # Get delivery info
    if delivery_df is not None and len(delivery_df) > 0:
        delivery = delivery_df.iloc[0]
        route_data['route_coords'] = extract_route_from_delivery(delivery)
        route_data['delivery_distance_km'] = delivery.get('distance_km', 10)
        route_data['weather'] = extract_weather_from_delivery(delivery)
        route_data['vehicle_type'] = delivery.get('vehicle_type', 'Two-wheeler')
        route_data['package_weight_kg'] = delivery.get('weight_kg', 2.0)
    else:
        # Fallback to synthetic route
        start_time = datetime.now()
        route_data['route_coords'] = [
            (28.6315 + i*0.0001, 77.2167 + i*0.00008, start_time + timedelta(minutes=i*2))
            for i in range(100)
        ]
        route_data['delivery_distance_km'] = 10.0
        route_data['weather'] = 'Clear'
        route_data['vehicle_type'] = 'Two-wheeler'
        route_data['package_weight_kg'] = 2.0
    
    # Get traffic-based delay
    if traffic_df is not None and len(traffic_df) > 0:
        traffic = traffic_df.iloc[0]
        route_data['standard_delay_minutes'] = extract_delay_from_traffic(traffic)
    else:
        # Fallback to default
        route_data['standard_delay_minutes'] = 25.0
    
    # Compute thermal penalty from weather
    route_data['thermal_penalty'] = weather_to_thermal_penalty(route_data['weather'])
    
    return route_data


# ─────────────────────────────────────────────────────────────────────────────
# MULTI-HOP VACCINE DISTRIBUTION FUNCTIONS (Cold Chain Pharmaceutical)
# ─────────────────────────────────────────────────────────────────────────────

def standardize_vaccine_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize vaccine dataset column names to match expected format.
    Handles multiple vaccine dataset formats (synthetic, Kaggle, etc.)
    
    Args:
        df: Raw vaccine DataFrame with any column naming convention
    
    Returns:
        DataFrame with standardized column names:
        [route_id, shipment_id, hop_number, origin_city, destination_city,
         vehicle_type, start_time, end_time, distance_km, duration_hours,
         temp_avg_celsius, temp_min_celsius, temp_max_celsius, humidity_avg_percent,
         compliance_status, alert_flags, batch_number, medication_type,
         min_temp_limit, max_temp_limit, ambient_weather]
    """
    # Column mapping: maps various possible column names to standard names
    col_mapping = {
        # Route/Shipment identifiers
        'Route_ID': 'route_id', 'route_id': 'route_id', 'Route_Id': 'route_id',
        'Shipment_ID': 'shipment_id', 'shipment_id': 'shipment_id', 'Shipment_Id': 'shipment_id',
        'Hop_Number': 'hop_number', 'hop_number': 'hop_number', 'Hop_Num': 'hop_number',
        'Hop': 'hop_number',
        
        # Location
        'Origin_City': 'origin_city', 'origin_city': 'origin_city', 'Start_City': 'origin_city',
        'Destination_City': 'destination_city', 'destination_city': 'destination_city', 'End_City': 'destination_city',
        
        # Vehicle
        'Vehicle_Type': 'vehicle_type', 'vehicle_type': 'vehicle_type', 'Transport_Mode': 'vehicle_type',
        
        # Time
        'Start_Time': 'start_time', 'start_time': 'start_time', 'Departure_Time': 'start_time',
        'End_Time': 'end_time', 'end_time': 'end_time', 'Arrival_Time': 'end_time',
        'Distance_KM': 'distance_km', 'distance_km': 'distance_km', 'Distance (km)': 'distance_km',
        'Duration_Hours': 'duration_hours', 'duration_hours': 'duration_hours', 'Duration (hours)': 'duration_hours',
        'Travel_Time': 'duration_hours', 'Transit_Duration': 'duration_hours',
        
        # Temperature
        'Temp_Avg_Celsius': 'temp_avg_celsius', 'temp_avg_celsius': 'temp_avg_celsius',
        'Temperature': 'temp_avg_celsius', 'Avg_Temperature': 'temp_avg_celsius',
        'Temp_Avg': 'temp_avg_celsius', 'Average_Temp': 'temp_avg_celsius',
        'Temp_Min_Celsius': 'temp_min_celsius', 'temp_min_celsius': 'temp_min_celsius',
        'Min_Temperature': 'temp_min_celsius', 'Temp_Min': 'temp_min_celsius',
        'Temp_Max_Celsius': 'temp_max_celsius', 'temp_max_celsius': 'temp_max_celsius',
        'Max_Temperature': 'temp_max_celsius', 'Temp_Max': 'temp_max_celsius',
        
        # Humidity
        'Humidity_Avg_Percent': 'humidity_avg_percent', 'humidity_avg_percent': 'humidity_avg_percent',
        'Humidity': 'humidity_avg_percent', 'Avg_Humidity': 'humidity_avg_percent',
        'Humidity_Avg': 'humidity_avg_percent',
        
        # Compliance
        'Compliance_Status': 'compliance_status', 'compliance_status': 'compliance_status',
        'Status': 'compliance_status', 'Compliance': 'compliance_status',
        'Alert_Flags': 'alert_flags', 'alert_flags': 'alert_flags', 'Alerts': 'alert_flags',
        
        # Batch/Medication
        'Batch_Number': 'batch_number', 'batch_number': 'batch_number', 'Batch_ID': 'batch_number',
        'Batch': 'batch_number',
        'Medication_Type': 'medication_type', 'medication_type': 'medication_type', 'Medicine': 'medication_type',
        'Vaccine': 'medication_type', 'Vaccine_Type': 'medication_type',
        
        # Limits
        'Min_Temp_Limit': 'min_temp_limit', 'min_temp_limit': 'min_temp_limit',
        'Temp_Min_Limit': 'min_temp_limit', 'Min_Limit': 'min_temp_limit',
        'Max_Temp_Limit': 'max_temp_limit', 'max_temp_limit': 'max_temp_limit',
        'Temp_Max_Limit': 'max_temp_limit', 'Max_Limit': 'max_temp_limit',
        
        # Weather
        'Ambient_Weather': 'ambient_weather', 'ambient_weather': 'ambient_weather',
        'Weather': 'ambient_weather', 'Weather_Condition': 'ambient_weather',
    }
    
    # Apply renaming
    df_copy = df.rename(columns=col_mapping)
    
    # Fill missing columns with defaults
    required_columns = {
        'route_id': 'ROUTE_AUTO',
        'shipment_id': 'SHIP_AUTO',
        'hop_number': 1,
        'origin_city': 'Unknown',
        'destination_city': 'Unknown',
        'vehicle_type': 'Generic',
        'start_time': datetime.now().isoformat(),
        'end_time': (datetime.now() + timedelta(hours=1)).isoformat(),
        'distance_km': 0.0,
        'duration_hours': 1.0,
        'temp_avg_celsius': 5.0,
        'temp_min_celsius': 2.0,
        'temp_max_celsius': 8.0,
        'humidity_avg_percent': 65.0,
        'compliance_status': 'unknown',
        'alert_flags': 'none',
        'batch_number': 'BATCH_UNKNOWN',
        'medication_type': 'Unknown_Vaccine',
        'min_temp_limit': 2.0,
        'max_temp_limit': 8.0,
        'ambient_weather': 'unknown',
    }
    
    for col, default in required_columns.items():
        if col not in df_copy.columns:
            df_copy[col] = default
    
    # Ensure numeric columns are actually numeric
    numeric_cols = ['distance_km', 'duration_hours', 'temp_avg_celsius', 'temp_min_celsius',
                   'temp_max_celsius', 'humidity_avg_percent', 'min_temp_limit', 'max_temp_limit']
    for col in numeric_cols:
        if col in df_copy.columns:
            df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce').fillna(0.0)
    
    # Convert hop_number to int
    if 'hop_number' in df_copy.columns:
        df_copy['hop_number'] = pd.to_numeric(df_copy['hop_number'], errors='coerce').fillna(1).astype(int)
    
    return df_copy


def load_vaccine_distribution_logs(
    filepath: str = "datasets/vaccine_distribution_temp_logs.csv",
    sample_size: int = 5
) -> Optional[pd.DataFrame]:
    """
    Load multi-hop vaccine distribution temperature logs.
    Works with multiple vaccine dataset formats (synthetic, Kaggle, etc.)
    Automatically standardizes column names to expected format.
    
    Args:
        filepath: Path to vaccine CSV file (synthetic or real Kaggle data)
        sample_size: Number of complete routes (not individual hops)
    
    Returns:
        DataFrame with standardized columns: [route_id, shipment_id, hop_number, 
                origin_city, destination_city, vehicle_type, temp_avg_celsius, 
                temp_min_celsius, temp_max_celsius, compliance_status, ...]
        Returns None if file not found
    """
    try:
        df = pd.read_csv(filepath)
        
        # Standardize all column names to expected format
        df = standardize_vaccine_columns(df)
        
        # Get unique route IDs
        unique_routes = df['route_id'].unique()
        selected_routes = np.random.choice(
            unique_routes, 
            size=min(sample_size, len(unique_routes)), 
            replace=False
        )
        
        # Filter to selected routes only
        result = df[df['route_id'].isin(selected_routes)].copy()
        return result.reset_index(drop=True)
        
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error loading vaccine distribution logs: {e}")
        return None


def extract_multihop_journey(vaccine_logs_df: Optional[pd.DataFrame]) -> Dict:
    """
    Extract a complete multi-hop journey from vaccine distribution logs.
    
    Args:
        vaccine_logs_df: DataFrame from load_vaccine_distribution_logs()
    
    Returns:
        Dict with keys {
            'route_id': str,
            'shipment_id': str,
            'hops': List[Dict] with hop details,
            'total_distance_km': float,
            'total_duration_hours': float,
            'medication_type': str,
            'batch_number': str,
            'compliance_status': str,
            'critical_alerts': List[str]
        }
    """
    if vaccine_logs_df is None or len(vaccine_logs_df) == 0:
        return None
    
    # Get first route
    route_data = vaccine_logs_df.iloc[0]
    route_id = route_data['route_id']
    
    # Extract all hops for this route
    route_hops = vaccine_logs_df[vaccine_logs_df['route_id'] == route_id].copy()
    route_hops = route_hops.sort_values('hop_number')
    
    hops_list = []
    for _, hop in route_hops.iterrows():
        hops_list.append({
            'hop_number': int(hop['hop_number']),
            'origin': hop['origin_city'],
            'destination': hop['destination_city'],
            'vehicle_type': hop['vehicle_type'],
            'distance_km': float(hop['distance_km']),
            'duration_hours': float(hop['duration_hours']),
            'start_time': hop['start_time'],
            'end_time': hop['end_time'],
            'temp_avg_c': float(hop['temp_avg_celsius']),
            'temp_min_c': float(hop['temp_min_celsius']),
            'temp_max_c': float(hop['temp_max_celsius']),
            'humidity_avg': float(hop['humidity_avg_percent']),
            'compliance_status': hop['compliance_status'],
            'alert_flags': hop['alert_flags'],
            'min_temp_limit': float(hop['min_temp_limit']),
            'max_temp_limit': float(hop['max_temp_limit']),
        })
    
    # Identify critical alerts
    critical_alerts = route_hops[
        route_hops['compliance_status'].isin(['critical', 'warning'])
    ]['alert_flags'].tolist()
    
    return {
        'route_id': route_id,
        'shipment_id': route_data['shipment_id'],
        'medication_type': route_data['medication_type'],
        'batch_number': route_data['batch_number'],
        'hops': hops_list,
        'total_distance_km': float(route_hops['distance_km'].sum()),
        'total_duration_hours': float(route_hops['duration_hours'].sum()),
        'compliance_status': 'critical' if any(s == 'critical' for s in route_hops['compliance_status']) else 'compliant',
        'critical_alerts': critical_alerts,
        'num_hops': len(hops_list)
    }


def calculate_cumulative_pis_degradation(
    multihop_journey: Dict,
    pis_calculator
) -> Dict:
    """
    Calculate cumulative Product Integrity Score degradation across all hops.
    
    Args:
        multihop_journey: Dict from extract_multihop_journey()
        pis_calculator: ProductIntegrityScore instance
    
    Returns:
        Dict with keys {
            'hop_pis_scores': List[float] (PIS score after each hop),
            'cumulative_degradation': float (0-100),
            'critical_hops': List[int] (hop indices with critical breaches),
            'final_pis_score': float,
            'overall_compliance': str ('PASS' or 'FAIL')
        }
    """
    hops = multihop_journey['hops']
    hop_scores = []
    current_pis = 100.0  # Start with perfect integrity
    
    for i, hop in enumerate(hops):
        # Temperature breach penalty
        temp_breach_penalty = 0.0
        
        if hop['temp_max_c'] > hop['max_temp_limit']:
            excess = hop['temp_max_c'] - hop['max_temp_limit']
            temp_breach_penalty += excess * 5  # 5 points per degree over limit
        
        if hop['temp_min_c'] < hop['min_temp_limit']:
            deficit = hop['min_temp_limit'] - hop['temp_min_c']
            temp_breach_penalty += deficit * 3  # 3 points per degree under limit
        
        # Duration penalty (longer transport = higher degradation risk)
        duration_penalty = hop['duration_hours'] * 2
        
        # Humidity penalty
        humidity_penalty = max(0, (hop['humidity_avg'] - 65) * 0.5)  # Baseline 65%
        
        # Total penalty for this hop
        hop_penalty = min(100, temp_breach_penalty + duration_penalty + humidity_penalty)
        current_pis -= hop_penalty * 0.1  # Scale penalty
        current_pis = max(0, current_pis)  # Can't go below 0
        
        hop_scores.append(round(current_pis, 2))
    
    # Identify critical hops
    critical_hops = []
    for i, hop in enumerate(hops):
        if hop['compliance_status'] == 'critical':
            critical_hops.append(i)
    
    overall_compliance = 'PASS' if current_pis >= 85 else 'FAIL'
    
    return {
        'hop_pis_scores': hop_scores,
        'cumulative_degradation': round(100 - current_pis, 2),
        'critical_hops': critical_hops,
        'final_pis_score': round(current_pis, 2),
        'overall_compliance': overall_compliance,
        'num_hops': len(hops)
    }


if __name__ == "__main__":
    # Test loading functions
    print("Testing Dataset Loader...")
    
    delivery_sample = load_delivery_logistics_sample()
    if delivery_sample is not None:
        print("✓ Loaded Delivery Logistics sample")
        print(delivery_sample.head())
    else:
        print("✗ Delivery Logistics CSV not found (expected: datasets/Delivery_Logistics.csv)")
    
    traffic_sample = load_delhi_traffic_sample()
    if traffic_sample is not None:
        print("✓ Loaded Delhi Traffic sample")
        print(traffic_sample.head())
    else:
        print("✗ Delhi Traffic CSVs not found")
    
    # Test creating a realistic route
    realistic_route = create_realistic_route(delivery_sample, traffic_sample)
    print("\nRealistic Route Data:")
    print(realistic_route)
