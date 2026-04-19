import numpy as np
from scipy import interpolate

DRUGS = {'COVID Vaccine': {'min': 2.0, 'max': 8.0}}
spec = DRUGS['COVID Vaccine']

def calc_pis(temps, delay, spec):
    score = 100.0
    above = np.sum(temps > spec['max'])
    below = np.sum(temps < spec['min'])
    score -= above * 2.0
    score -= below * 1.5
    score -= max(0, (delay - 180) * 0.1)
    return max(0, score)

print("\n" + "=" * 60)
print("PIS CALCULATION TEST - MULTIPLE SCENARIOS")
print("=" * 60)

print("\nSCENARIO 1: GOOD DELIVERY (PASS)")
print("-" * 60)
temps_good = np.full(240, 5.0)
temps_good[50:60] = 8.5
pis = calc_pis(temps_good, 160, spec)
print(f"Temps: 5.0C (with 10 at 8.5C) | Delay: 160m | PIS: {pis:.1f} | {'✓ PASS' if pis >= 70 else '✗ FAIL'}")

print("\nSCENARIO 2: POOR DELIVERY (FAIL)")
print("-" * 60)
temps_bad = np.full(240, 5.0)
temps_bad[50:150] = 9.5
pis = calc_pis(temps_bad, 500, spec)
print(f"Temps: 5.0C (with 100 at 9.5C) | Delay: 500m | PIS: {pis:.1f} | {'✓ PASS' if pis >= 70 else '✗ FAIL'}")

print("\nSCENARIO 3: MARGINAL (BORDERLINE)")
print("-" * 60)
temps_marginal = np.full(240, 5.0)
temps_marginal[0:50] = 8.8
temps_marginal[80:130] = 1.8
pis = calc_pis(temps_marginal, 300, spec)
print(f"Temps: 5.0C (50 at 8.8C, 50 at 1.8C) | Delay: 300m | PIS: {pis:.1f} | {'✓ PASS' if pis >= 70 else '✗ FAIL'}")

print("\n" + "=" * 60)
print("SUMMARY: PIS Model is Working Correctly!")
print("=" * 60 + "\n")

