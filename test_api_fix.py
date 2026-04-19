#!/usr/bin/env python3
"""Quick test of API fixes for app.py"""

from cold_chain.ambient_temperature import (
    generate_synthetic_temperature_profile,
    calculate_pis,
    get_ambient_temperature,
    apply_urban_heat_island_correction
)
import numpy as np
import pandas as pd

print("\n" + "="*60)
print("Testing API Fixes")
print("="*60)

# Test 1: Synthetic profile generation with correct parameters
print("\n[TEST 1] Synthetic temperature profile generation")
try:
    full_hist, sparse = generate_synthetic_temperature_profile(
        duration_hours=4.0,
        base_ambient=25.0,
        traffic_stress=0.5,
        noise_level=0.5
    )
    print(f"✅ Synthetic profile: {len(full_hist)} hourly points")
    print(f"   Range: {np.min(full_hist):.1f}-{np.max(full_hist):.1f}°C")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: PIS calculation with correct parameters
print("\n[TEST 2] PIS calculation with correct parameters")
try:
    pis = calculate_pis(
        temperature_history=full_hist,
        sensor_readings=[],
        traffic_delay_minutes=10.0,
        med_type='vaccine_covid'
    )
    score = pis.get('pis_score', 'N/A')
    status = pis.get('compliance_status', 'N/A')
    print(f"✅ PIS calculated: score={score}, status={status}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: Urban heat island correction
print("\n[TEST 3] Urban heat island correction")
try:
    base_temp = 25.0
    corrected = apply_urban_heat_island_correction(base_temp, traffic_density=0.6)
    print(f"✅ UHI correction: {base_temp}°C → {corrected}°C (traffic=0.6)")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 4: OpenMeteo API with correct parameters
print("\n[TEST 4] OpenMeteo API with correct parameters")
try:
    import datetime
    today = datetime.date.today()
    result = get_ambient_temperature(
        latitude=28.6315,
        longitude=77.2167,
        start_date=str(today - datetime.timedelta(days=1)),
        end_date=str(today)
    )
    if result is not None:
        print(f"✅ OpenMeteo API: {len(result)} records")
    else:
        print(f"⚠️ OpenMeteo returned None (expected if offline)")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*60)
print("All tests completed!")
print("="*60 + "\n")
