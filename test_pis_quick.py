#!/usr/bin/env python
"""Quick test of PIS fix"""

import pandas as pd
from cold_chain.integrity_score import compute_product_integrity_score

# Create test data
df = pd.DataFrame({
    'timestamp': [pd.Timestamp('2026-04-18 10:00'), pd.Timestamp('2026-04-18 10:30')],
    'temp_celsius': [5.0, 5.5],
    'lat': [28.6315, 28.6315],
    'lon': [77.2167, 77.2167]
})

# Call function
result = compute_product_integrity_score(
    df, 
    0,  # no delay
    [],  # no ambient data
    {
        'name': 'COVID',
        'min_temp_celsius': 2.0,
        'max_temp_celsius': 8.0,
        'excursion_tolerance_minutes': 60
    }
)

print("Result keys:", list(result.keys()))
print("compliance_status:", result.get('compliance_status', "NOT FOUND"))
print("score:", result.get('score'))
print("grade:", result.get('grade'))
print("\n✓ Test passed!" if 'compliance_status' in result else "\n✗ Test failed!")
