# Cold Chain — Using Real Kaggle Datasets

This guide explains how to set up the **Option A** approach for realistic cold chain simulations using real Kaggle datasets.

## Overview

The cold chain simulation now supports loading real data from two Kaggle datasets:
1. **Delhi Traffic Dataset** — Real routes, distances, travel times, delays
2. **Delivery Logistics Dataset (India)** — Real weather, vehicle types, package weights, delivery metrics

If these datasets are not available, the simulation gracefully falls back to **synthetic data**.

---

## Step 1: Download Kaggle Datasets

### Dataset 1: Delhi Traffic Travel Time Dataset
- **Kaggle URL**: https://www.kaggle.com/datasets/algozee/traffic-data-set
- **Files needed**:
  - `delhi_traffic_features.csv`
  - `delhi_traffic_target.csv`

### Dataset 2: Delivery Logistics Dataset (India – Multi-Partner)
- **Kaggle URL**: https://www.kaggle.com/datasets/muhammadahmaddaar/delivery-logistics-dataset-india-multi-partner
- **Files needed**:
  - `Delivery_Logistics.csv`

---

## Step 2: Place Datasets in Project

Create a `datasets/` directory in your JaamCTRL project root and place the CSVs there:

```
JaamCTRL/
├── app.py
├── requirements.txt
├── datasets/                    # NEW DIRECTORY
│   ├── delhi_traffic_features.csv
│   ├── delhi_traffic_target.csv
│   └── Delivery_Logistics.csv
├── cold_chain/
│   ├── __init__.py
│   ├── dataset_loader.py        # NEW - loads these CSVs
│   ├── integrity_score.py
│   ├── temperature_reconstructor.py
│   └── ambient_overlay.py
├── src/
└── sumo/
```

---

## Step 3: How the Data Flows

### Cold Chain Tab Workflow

When you click **"Simulate Cold Chain Run"** in the app:

1. **Dataset Loader** attempts to load:
   - 1 random delivery from `Delivery_Logistics.csv`
   - 1 random trip from Delhi traffic CSVs
   
2. **Route Creation**:
   - Extracts real distance (km), weather, vehicle type, package weight
   - Generates realistic coordinates spanning Delhi city bounds
   - Maps real travel time delays into route timing

3. **Temperature Simulation**:
   - Uses realistic **baseline delay** from delivery dataset (actual value, not hardcoded 25 min)
   - Adjusts thermal penalty based on **real weather** (Clear/Rain/Fog affects ambient temp)
   - Compares: Standard routing vs JaamCTRL-optimized routing

4. **Results**:
   - Shows which dataset was used (Kaggle vs Synthetic)
   - Displays weather conditions and delay reduction estimate
   - PIS score reflects realistic conditions

### Data Sources

**From `Delivery_Logistics.csv`**:
- Distance (km) — route length
- Delivery Time — actual delivery time taken
- Expected Time — baseline for delay calculation
- Weather Condition — affects thermal penalty (×0.85 for rain, ×1.3 for sunny, etc.)
- Vehicle Type — Two-wheeler, Motorcycle, Auto, etc.
- Package Weight (kg) — context for cold chain size

**From Delhi Traffic**:
- Distance, Travel Time, Expected Time — real delay metrics
- Weather, Traffic Density — environmental factors

---

## Step 4: What If Datasets Aren't Available?

The app includes **graceful fallback logic**:

```python
try:
    # Load real Kaggle data
    delivery_df = load_delivery_logistics_sample(filepath=...)
    traffic_df = load_delhi_traffic_sample(...)
    route_data = create_realistic_route(delivery_df, traffic_df)
    data_source = "Kaggle (Real Data)"
except:
    # Fall back to synthetic if files missing
    route_coords = [synthetic Delhi route]
    std_delay = 25.0  # default
    weather = "Clear"
    data_source = "Synthetic"
```

**UI Feedback**: 
- ✓ Real data: `Data source: Kaggle (Real Data) | Weather: Rain | Baseline delay: 22.5 min`
- Fallback: `Data source: Synthetic (Kaggle datasets not found...)`

---

## Step 5: Dataset Columns Reference

### `delhi_traffic_features.csv` (Expected columns)

| Column | Type | Example | Use |
|--------|------|---------|-----|
| Trip_ID | int | 1001 | Route identifier |
| distance_km | float | 12.5 | Route distance |
| traffic_density | str | High/Medium/Low | Traffic congestion level |
| weather | str | Clear/Rain/Fog | Environmental conditions |
| time_of_day | str | Morning Peak/Afternoon | Temporal factor |
| day_type | str | Weekday/Weekend | Temporal factor |
| road_type | str | Highway/Main Road | Infrastructure type |
| average_speed_kmh | float | 18.5 | Traffic speed |

### `delhi_traffic_target.csv`

| Column | Type | Example | Use |
|--------|------|---------|-----|
| Trip_ID | int | 1001 | Route identifier (joins with features) |
| travel_time | int | 45 | Actual time taken (minutes) |

### `Delivery_Logistics.csv` (Expected columns)

| Column | Type | Example | Use |
|--------|------|---------|-----|
| Delivery ID | str | DEL001 | Delivery identifier |
| Distance | float | 8.3 | Route distance (km) |
| Delivery Time | int | 35 | Actual delivery time (min) |
| Expected Time | int | 30 | Expected baseline time (min) |
| Weather Condition | str | Clear/Rain | Affects thermal penalty |
| Vehicle Type | str | Two-wheeler | Transport mode |
| Package Weight | float | 2.5 | Package mass (kg) |

---

## Step 6: Understanding the Data Loader Functions

### `dataset_loader.py` Functions

```python
# Load deliveries from Kaggle
delivery_sample = load_delivery_logistics_sample(
    filepath="datasets/Delivery_Logistics.csv",
    sample_size=1  # Get 1 random delivery
)

# Load traffic trips from Kaggle
traffic_sample = load_delhi_traffic_sample(
    features_path="datasets/delhi_traffic_features.csv",
    target_path="datasets/delhi_traffic_target.csv",
    sample_size=1
)

# Create realistic route combining both
route_data = create_realistic_route(delivery_sample, traffic_sample)
```

Returns a dict with:
- `route_coords` — GPS coordinates with timestamps
- `delivery_distance_km` — actual distance
- `standard_delay_minutes` — real delay = actual_time - expected_time
- `weather` — actual weather condition
- `vehicle_type` — transport mode
- `package_weight_kg` — package mass
- `thermal_penalty` — weather multiplier (0.85–1.3)

---

## Testing the Integration

### Test 1: Verify Dataset Loading

```bash
cd cold_chain
python dataset_loader.py
```

Expected output:
```
Testing Dataset Loader...
✓ Loaded Delivery Logistics sample
✓ Loaded Delhi Traffic sample
...
Realistic Route Data:
{'route_coords': [...], 'delivery_distance_km': 12.5, ...}
```

### Test 2: Run App with Real Data

```bash
streamlit run app.py
```

1. Navigate to **Cold Chain** tab
2. Select drug profile (COVID_Vaccine, Insulin, or Blood_Plasma)
3. Click **Simulate Cold Chain Run**
4. Check the info box for data source

Expected:
- ✓ `Data source: Kaggle (Real Data)` if CSVs found
- ⚠️ `Data source: Synthetic` if CSVs not found (OK, graceful fallback)

---

## Troubleshooting

### Issue: "FileNotFoundError: datasets/Delivery_Logistics.csv not found"

**Solution**: 
1. Create `datasets/` folder in project root
2. Download CSV from Kaggle
3. Verify file path is exactly: `c:\Users\hp\OneDrive\Desktop\JaamCTRL\datasets\Delivery_Logistics.csv`

### Issue: Column name mismatch

**Solution**:
- Dataset loader includes `col_mapping` dictionary that auto-renames common column variations
- If still failing, check actual column names in your CSV and update `col_mapping` in `dataset_loader.py`

### Issue: Empty or corrupted CSV

**Solution**:
- Verify CSV opens in Excel without errors
- Check file size is reasonable (Delivery_Logistics should be ~3.7 MB)
- Re-download from Kaggle

---

## Performance Impact

- **With real data**: Slightly slower on first load (CSV parsing ~100-500ms) but data is cached in `st.session_state`
- **Synthetic fallback**: Instant generation (<50ms)
- **Recommended**: Run simulations with real data for presentations, use synthetic for rapid testing

---

## Next Steps

After setting up the datasets:

1. Run the cold chain tab and verify real data is loading
2. Compare PIS scores across different weather conditions and vehicle types
3. Analyze how traffic delays correlate with temperature excursions
4. Document findings for Hack Helix T3-P02 submission

---

**Questions?** Check `cold_chain/dataset_loader.py` for implementation details.
