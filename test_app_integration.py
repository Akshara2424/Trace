"""
test_app_integration.py
-----------------------
Quick integration test for app.py cold chain tab compatibility
"""

import sys
import os

# Test imports
print("Testing cold_chain module imports...")

try:
    from cold_chain.integrity_score import DRUG_PROFILES, compute_product_integrity_score
    print("✓ integrity_score module imported")
except ImportError as e:
    print(f"✗ Failed to import integrity_score: {e}")
    sys.exit(1)

try:
    from cold_chain.temperature_reconstructor import (
        generate_sparse_sensor_logs, reconstruct_temperature_history
    )
    print("✓ temperature_reconstructor module imported")
except ImportError as e:
    print(f"✗ Failed to import temperature_reconstructor: {e}")
    sys.exit(1)

try:
    from cold_chain.ambient_overlay import traffic_density_to_thermal_penalty
    print("✓ ambient_overlay module imported")
except ImportError as e:
    print(f"✗ Failed to import ambient_overlay: {e}")
    sys.exit(1)

# Test DRUG_PROFILES
print("\nTesting DRUG_PROFILES...")
expected_profiles = ["COVID_Vaccine", "Insulin", "Blood_Plasma"]
for profile in expected_profiles:
    if profile in DRUG_PROFILES:
        print(f"✓ {profile} profile available")
    else:
        print(f"✗ {profile} profile missing")
        sys.exit(1)

# Test quick functionality
print("\nTesting quick cold-chain workflow...")
import pandas as pd
from datetime import datetime, timedelta

try:
    # Create synthetic route
    start = datetime.now()
    route = [(28.6315 + i*0.0001, 77.2167, start + timedelta(minutes=i)) for i in range(20)]
    
    # Generate sparse sensors
    sparse = generate_sparse_sensor_logs(route, n_sensors=3, duration_minutes=30)
    print(f"✓ Generated {len(sparse)} sparse sensor readings")
    
    # Reconstruct temperature
    reconstructed = reconstruct_temperature_history(sparse, route)
    print(f"✓ Reconstructed {len(reconstructed)} temperature points")
    
    # Apply thermal penalties
    heatmap = [[28.6315, 77.2167, 0.5]]
    augmented = traffic_density_to_thermal_penalty(heatmap, base_temp=25.0)
    print(f"✓ Applied thermal penalties to {len(augmented)} heatmap points")
    
    # Compute PIS
    covid = DRUG_PROFILES["COVID_Vaccine"]
    pis = compute_product_integrity_score(reconstructed, 10.0, [], covid)
    print(f"✓ Computed PIS: {pis['score']:.0f}/100 (Grade: {pis['grade']})")
    
except Exception as e:
    print(f"✗ Workflow test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("✓ All integration tests passed!")
print("="*60)
print("\nThe app.py Cold Chain Monitor tab is ready to use.")
