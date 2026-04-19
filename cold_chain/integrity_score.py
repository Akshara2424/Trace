"""
integrity_score.py
------------------
Product Integrity Score (PIS) for pharmaceutical cold-chain monitoring.
Computes damage risk from thermal excursions, delays, and routes.
"""

import pandas as pd
from typing import Dict, List, Any


# Preset drug profiles: {name, min/max temp (°C), excursion tolerance (min)}
DRUG_PROFILES = {
    'COVID_Vaccine': {
        'name': 'COVID_Vaccine',
        'min_temp_celsius': 2.0,
        'max_temp_celsius': 8.0,
        'excursion_tolerance_minutes': 60
    },
    'Insulin': {
        'name': 'Insulin',
        'min_temp_celsius': 2.0,
        'max_temp_celsius': 8.0,
        'excursion_tolerance_minutes': 30
    },
    'Blood_Plasma': {
        'name': 'Blood_Plasma',
        'min_temp_celsius': 1.0,
        'max_temp_celsius': 6.0,
        'excursion_tolerance_minutes': 20
    }
}


def compute_product_integrity_score(
    reconstructed_temps: pd.DataFrame,
    traffic_delay_minutes: float,
    ambient_data: List[List[float]],
    drug_profile: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compute Product Integrity Score (0-100) for a pharmaceutical batch.
    
    Args:
        reconstructed_temps: DataFrame with columns [timestamp, lat, lon, temp_celsius]
        traffic_delay_minutes: Additional delay from traffic vs. optimal routing
        ambient_data: List of [lat, lon, weight, ambient_temp] (for context)
        drug_profile: Dict with keys [name, min_temp_celsius, max_temp_celsius, 
                     excursion_tolerance_minutes]
    
    Returns:
        Dict with keys:
            - score: PIS (0-100)
            - grade: Letter grade (A/B/C/F)
            - flag_for_inspection: Boolean (True if score < 70)
            - deductions_breakdown: Dict of deduction categories
            - primary_risk_factor: String identifying largest threat
    """
    score = 100.0
    deductions = {}
    
    min_temp = drug_profile['min_temp_celsius']
    max_temp = drug_profile['max_temp_celsius']
    tolerance = drug_profile['excursion_tolerance_minutes']
    
    # Calculate sample interval (minutes between readings)
    if len(reconstructed_temps) < 2:
        sample_interval = 1.0
    else:
        sample_interval = (reconstructed_temps['timestamp'].iloc[1] - 
                          reconstructed_temps['timestamp'].iloc[0]).total_seconds() / 60
    
    # 1. Deduction: Time above max temperature (-2 pts/min)
    above_max = reconstructed_temps[reconstructed_temps['temp_celsius'] > max_temp]
    minutes_above_max = len(above_max) * sample_interval
    deduct_above = minutes_above_max * 2.0
    deductions['above_max_temp'] = {'minutes': minutes_above_max, 'deduction': deduct_above}
    score -= deduct_above
    
    # 2. Deduction: Time below minimum temperature (-1.5 pts/min)
    below_min = reconstructed_temps[reconstructed_temps['temp_celsius'] < min_temp]
    minutes_below_min = len(below_min) * sample_interval
    deduct_below = minutes_below_min * 1.5
    deductions['below_min_temp'] = {'minutes': minutes_below_min, 'deduction': deduct_below}
    score -= deduct_below
    
    # 3. Deduction: Traffic delay impact (-0.5 pts/min)
    deduct_delay = traffic_delay_minutes * 0.5
    deductions['traffic_delay'] = {'minutes': traffic_delay_minutes, 'deduction': deduct_delay}
    score -= deduct_delay
    
    # 4. Deduction: Distinct excursion events (-5 pts each)
    # Excursion = time outside tolerance AND outside range (combined threat)
    excursion_count = 0
    if len(above_max) > 0 or len(below_min) > 0:
        combined_out_of_range = pd.concat([above_max, below_min]).drop_duplicates(
            subset=['timestamp']
        ).sort_values('timestamp')
        
        # Count distinct events (separated by >5 min gaps)
        prev_ts = None
        for _, row in combined_out_of_range.iterrows():
            if prev_ts is None or (row['timestamp'] - prev_ts).total_seconds() > 300:
                excursion_count += 1
            prev_ts = row['timestamp']
    
    deduct_events = excursion_count * 5.0
    deductions['excursion_events'] = {'count': excursion_count, 'deduction': deduct_events}
    score -= deduct_events
    
    # Clamp score to [0, 100]
    score = max(0.0, min(100.0, score))
    
    # Assign grade based on score
    if score >= 90:
        grade = 'A'
    elif score >= 75:
        grade = 'B'
    elif score >= 70:
        grade = 'C'
    else:
        grade = 'F'
    
    # Flag for inspection
    flag_for_inspection = score < 70
    
    # Identify primary risk factor (largest deduction)
    max_deduction_key = max(
        deductions.keys(),
        key=lambda k: deductions[k]['deduction']
    )
    primary_risk = max_deduction_key
    
    # Determine compliance status
    compliance_status = 'FAIL' if flag_for_inspection else 'PASS'
    
    return {
        'score': round(score, 2),
        'grade': grade,
        'compliance_status': compliance_status,
        'flag_for_inspection': flag_for_inspection,
        'deductions_breakdown': deductions,
        'primary_risk_factor': primary_risk,
        'total_deductions': round(100.0 - score, 2)
    }


def compare_routing_scenarios(
    standard_delay_minutes: float,
    jaamctrl_delay_minutes: float,
    reconstructed_temps: pd.DataFrame,
    drug_profile: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compare Product Integrity Score across routing scenarios.
    
    Args:
        standard_delay_minutes: Traffic delay for standard routing
        jaamctrl_delay_minutes: Traffic delay for JaamCTRL-optimized routing
        reconstructed_temps: Temperature data (assumed same for both routes)
        drug_profile: Pharmaceutical specification dict
    
    Returns:
        Dict with keys:
            - standard_score: PIS for standard routing
            - jaamctrl_score: PIS for JaamCTRL routing
            - pis_improvement_pct: Percentage improvement (0-100 scale)
            - faster: Boolean (True if JaamCTRL is faster)
            - time_saved_minutes: Minutes saved by JaamCTRL route
            - recommendation: String advice
    """
    # Ambient data is not strictly needed for this comparison, use empty list
    ambient_dummy = []
    
    # Score standard routing
    standard_result = compute_product_integrity_score(
        reconstructed_temps, standard_delay_minutes, ambient_dummy, drug_profile
    )
    
    # Score JaamCTRL routing
    jaamctrl_result = compute_product_integrity_score(
        reconstructed_temps, jaamctrl_delay_minutes, ambient_dummy, drug_profile
    )
    
    standard_pis = standard_result['score']
    jaamctrl_pis = jaamctrl_result['score']
    
    # Calculate improvement as percentage of standard score
    if standard_pis > 0:
        improvement_pct = ((jaamctrl_pis - standard_pis) / standard_pis) * 100
    else:
        improvement_pct = 0.0
    
    time_saved = standard_delay_minutes - jaamctrl_delay_minutes
    faster = time_saved > 0
    
    # Recommendation
    if jaamctrl_pis >= 90:
        recommendation = "✓ Use JaamCTRL route: excellent product safety"
    elif jaamctrl_pis > standard_pis:
        recommendation = f"✓ Use JaamCTRL route: {improvement_pct:.1f}% integrity improvement"
    else:
        recommendation = "✗ Standard route preferable: no significant improvement"
    
    return {
        'standard_score': standard_pis,
        'jaamctrl_score': jaamctrl_pis,
        'pis_improvement_pct': round(improvement_pct, 2),
        'faster': faster,
        'time_saved_minutes': round(time_saved, 2),
        'standard_grade': standard_result['grade'],
        'jaamctrl_grade': jaamctrl_result['grade'],
        'recommendation': recommendation
    }


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


if __name__ == '__main__':
    # Test block
    print("=" * 70)
    print("Testing integrity_score.py")
    print("=" * 70)
    
    # Create mock reconstructed temperature data
    import numpy as np
    from datetime import datetime, timedelta
    
    start = datetime.now()
    timestamps = [start + timedelta(minutes=i*2) for i in range(100)]
    
    # Simulated temps: mostly within range, with some excursions
    temps = 6.0 + np.random.normal(0.3, 0.5, 100)
    temps[20:25] = [8.5, 9.0, 8.8, 8.2, 7.5]  # Above max excursion
    temps[70:75] = [0.5, 0.3, 0.8, 1.2, 1.5]  # Below min excursion
    
    reconstructed = pd.DataFrame({
        'timestamp': timestamps,
        'lat': [28.63] * 100,
        'lon': [77.21] * 100,
        'temp_celsius': temps
    })
    
    print("\n[Test 1] COVID Vaccine PIS Calculation")
    covid_profile = DRUG_PROFILES['COVID_Vaccine']
    pis_covid = compute_product_integrity_score(
        reconstructed, 
        traffic_delay_minutes=15.0,
        ambient_data=[],
        drug_profile=covid_profile
    )
    print(f"  Score: {pis_covid['score']}/100 (Grade: {pis_covid['grade']})")
    print(f"  Primary Risk: {pis_covid['primary_risk_factor']}")
    print(f"  Flag for Inspection: {pis_covid['flag_for_inspection']}")
    for key, val in pis_covid['deductions_breakdown'].items():
        print(f"    - {key}: {val['deduction']:.1f} pts")
    
    print("\n[Test 2] Insulin PIS Calculation")
    insulin_profile = DRUG_PROFILES['Insulin']
    pis_insulin = compute_product_integrity_score(
        reconstructed,
        traffic_delay_minutes=5.0,
        ambient_data=[],
        drug_profile=insulin_profile
    )
    print(f"  Score: {pis_insulin['score']}/100 (Grade: {pis_insulin['grade']})")
    print(f"  Primary Risk: {pis_insulin['primary_risk_factor']}")
    
    print("\n[Test 3] Routing Scenario Comparison")
    comparison = compare_routing_scenarios(
        standard_delay_minutes=25.0,
        jaamctrl_delay_minutes=12.0,
        reconstructed_temps=reconstructed,
        drug_profile=covid_profile
    )
    print(f"  Standard Route PIS: {comparison['standard_score']}/100 ({comparison['standard_grade']})")
    print(f"  JaamCTRL Route PIS: {comparison['jaamctrl_score']}/100 ({comparison['jaamctrl_grade']})")
    print(f"  Improvement: {comparison['pis_improvement_pct']}%")
    print(f"  Time Saved: {comparison['time_saved_minutes']} minutes")
    print(f"  Recommendation: {comparison['recommendation']}")
    
    print("\n" + "=" * 70)
