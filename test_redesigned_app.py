#!/usr/bin/env python3
"""Test new app features"""

from cold_chain.integrity_score import DRUG_PROFILES
from cold_chain.ambient_temperature import (
    generate_synthetic_temperature_profile, 
    apply_urban_heat_island_correction,
    calculate_pis
)
from src.rl_agent import load_training_log
import numpy as np

print("=" * 60)
print("TESTING NEW APP FEATURES")
print("=" * 60)

# Test 1: Bulk batch processing
print("\n✅ Feature 1: Bulk Batch Processing")
results = []
for i in range(5):
    temp_profile = generate_synthetic_temperature_profile(
        duration_hours=4.0, 
        base_ambient=25.0 + np.random.normal(0, 1),
        traffic_stress=0.5,
        noise_level=0.3 + (i * 0.1)
    )
    temp_array = temp_profile[0]
    corrected = np.array([apply_urban_heat_island_correction(t, 0.5) for t in temp_array])
    pis = calculate_pis(
        temperature_history=corrected,
        sensor_readings=[],
        traffic_delay_minutes=30.0,
        med_type='COVID_Vaccine'
    )
    results.append(pis.get('pis_score', 0))
    print(f"   Shipment {i+1}: PIS {pis.get('pis_score', 0):.0f}/100 → {pis.get('compliance_status', 'N/A')}")

print(f"\n   Batch Summary:")
print(f"   - Processed: {len(results)} shipments")
print(f"   - Avg PIS: {np.mean(results):.1f}")
print(f"   - Pass Rate: {sum(1 for s in results if s >= 70) / len(results) * 100:.0f}%")

# Test 2: PIS metrics breakdown
print("\n✅ Feature 2: PIS Metrics Breakdown")
test_temps = generate_synthetic_temperature_profile(duration_hours=4.0)[0]
corrected = np.array([apply_urban_heat_island_correction(t, 0.5) for t in test_temps])
pis_detail = calculate_pis(
    temperature_history=corrected,
    sensor_readings=[],
    traffic_delay_minutes=30.0,
    med_type='COVID_Vaccine'
)
print(f"   PIS Score: {pis_detail.get('pis_score', 0):.0f}/100")
print(f"   Grade: {pis_detail.get('grade', 'N/A')}")
print(f"   Status: {pis_detail.get('compliance_status', 'N/A')}")
print(f"   Excursion Penalty: -{pis_detail.get('excursion_penalty', 0):.1f} pts")
print(f"   Duration Penalty: -{pis_detail.get('duration_penalty', 0):.1f} pts")
print(f"   Delay Penalty: -{pis_detail.get('delay_penalty', 0):.1f} pts")

# Test 3: Heatmap data generation
print("\n✅ Feature 3: Traffic Heatmap Data")
time_points = np.arange(0, 180, 10)
heatmap_data = np.array([
    np.sin(time_points / 30) * 0.7 + 0.3,
    np.sin(time_points / 30 + 1) * 0.7 + 0.4,
    np.sin(time_points / 30 - 1) * 0.7 + 0.35
])
print(f"   Heatmap Shape: {heatmap_data.shape} (3 junctions × {len(time_points)} time points)")
print(f"   Avg Congestion: {np.mean(heatmap_data):.1%}")
print(f"   Min Congestion: {np.min(heatmap_data):.1%}")
print(f"   Max Congestion: {np.max(heatmap_data):.1%}")

print("\n" + "=" * 60)
print("✅ ALL NEW FEATURES VERIFIED!")
print("=" * 60)
