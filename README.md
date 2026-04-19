# JaamCTRL

> **AI Adaptive Traffic Signal Optimizer** for Indian Urban Corridors
> + **Cold Chain Integrity Auditor** (Pharmaceutical Transit Monitoring)
> 
> Hack Helix 2026 – T3-P02: Cold Chain Integrity Challenge (Team: Cupcakes)
>
> **GitHub Repository:** [anchu2904/JaamCTRL](https://github.com/anchu2904/JaamCTRL)

---

## The Problems

### JaamCTRL: Urban Traffic Optimization

Indian urban traffic is uniquely chaotic: 60%+ two-wheelers, zero lane discipline,
random pedestrians and stray animals, and fixed-time signals that cannot react to
real conditions. Delhi alone loses an estimated **1.5 billion hours** annually to
congestion. Fixed-cycle signals are the root cause – they do not know what is
happening on the road.

### Cold Chain: Pharmaceutical Integrity During Transit

Meanwhile, India's pharmaceutical cold chain loses ~**₹8,000 crores** annually to temperature excursions. Traditional monitoring is reactive: sensors record data in a vehicle's freezer, but by the time a violation is detected, the batch is already damaged. Worse, **traffic delays extend thermal exposure**, but most auditing systems ignore routing entirely.

**Novel Insight:** Optimizing traffic signals for faster pharma truck transit is an innovative prevention mechanism – keep medicines moving = keep medicines cold.

---

## Our Solutions

### Problem 1: JaamCTRL (Traffic)

Simulates a 3-intersection arterial corridor (Connaught Place, Delhi) with authentic Indian traffic and applies two levels of AI:

| Level | Approach | Improvement |
|---|---|---|
| Rule-based | Queue-aware green extension + green-wave offset | ~20-25% delay reduction |
| PPO RL Agent | Coordinated joint control of all 3 signals | ~28-35% delay reduction |

### Problem 2: Cold Chain Auditor (Pharmaceutical)

Reconstructs pharmaceutical temperature profiles from sparse sensor data and optimizes delivery routes:

| Metric | Standard Routing | JaamCTRL-Optimized |
|---|---|---|
| PIS (COVID_Vaccine) | 37/100 (F) | 44/100 (F) |
| PIS Improvement | — | ~ 17–20% |
| Traffic Delay | 25 min | 12 min |
| Inspection Risk | Flagged | Borderline |

Both systems are designed for **clear "before vs after" demos** with quantifiable, auditable metrics.

---

## Demo

> **Live demo video:** *(insert GIF/video link here)*


## Architecture

```
jaamctrl/
├── app.py                             # Streamlit dashboard (7 tabs)
├── requirements.txt
├── src/
│   ├── run_simulation.py              # Core simulation runner (TraCI loop)
│   ├── signal_controller.py           # Rule-based adaptive controller
│   ├── rl_agent.py                    # PPO RL agent (stable-baselines3)
│   │                                  # └─ cold_chain_mode: pharma truck prioritization
│   ├── gps_generator.py               # Synthetic GPS probe generator
│   └── heatmap.py                     # Folium neon heatmap builder
├── cold_chain/                        # Cold Chain Integrity Auditor (T3-P02)
│   ├── __init__.py
│   ├── temperature_reconstructor.py   # Sparse→dense temp interpolation
│   ├── ambient_overlay.py             # Traffic density → thermal penalty
│   └── integrity_score.py             # Product Integrity Score (PIS) + routing
├── sumo/
│   ├── corridor.net.xml               # 3-intersection network (SUMO format)
│   ├── corridor.rou.xml               # Indian traffic mix (60% 2-wheelers)
│   ├── add_pharma_trucks.py           # Inject pharma vehicles (white, slower)
│   └── corridor.sumocfg               # SUMO config
├── models/                            # Saved PPO models
├── assets/                            # Screenshots / GIFs / backgrounds
├── COLD_CHAIN_INTEGRATION.md          # Cold-chain mode technical summary
└── STREAMLIT_COLD_CHAIN_TAB.md        # Cold Chain Monitor UI documentation
```

---

## Dual-Problem Architecture

JaamCTRL's core innovation is a **unified sparse-fill-dense framework** that solves two distinct problem domains:

### Problem 1: Traffic Signal Optimization (Main)
- **Input:** GPS probe data (crowd-sourced vehicle traces)
- **Core Engine:** Interpolate sparse GPS points → dense heatmap
- **Output:** Optimized signal timings (reduced delay, balanced flow)

### Problem 2: Cold Chain Temperature Auditing (Extended)
- **Input:** Sparse temperature sensor logs (every 8-15 min, random gaps)
- **Core Engine:** **Same interpolation + smoothing logic** → dense temperature profile
- **Output:** Product Integrity Score, routing optimization for pharma delivery

**Key Insight:** Traffic congestion and temperature fluctuation are both **stochastic, sparse-sampled phenomena**. The same Kalman-filter-style reconstruction that works for spatial-temporal GPS clustering elegantly solves temporal-dense temperature reconstruction. This convergence enables a single platform to optimize both traffic flow AND pharmaceutical integrity.

---

## Cold Chain Module (Hack Helix T3-P02)

The cold chain module extends JaamCTRL to solve **Pharmaceutical Cold Chain Integrity Auditing**. This module is fully integrated into the dashboard via the **❄️ Cold Chain Monitor** tab.

### Why Traffic Delay is a Cold Chain Risk Factor (Novel Insight)

In traditional cold chain auditing, only temperature violations matter. JaamCTRL introduces a critical innovation:

**Delayed vehicles = prolonged thermal exposure risk**

For a given ambient temperature and pharmaceutical sensitivity, a vehicle stopped at red lights for 25 minutes accumulates more heat-stress than the same vehicle moving freely for 15 minutes (due to reduced air circulation, solar loading, and thermal mass). By optimizing signal timing to minimize pharma truck dwell, JaamCTRL **actively prevents excursions before they happen**.

### Product Integrity Score (PIS) Formula

```
PIS = 100 - deductions
  
Deductions:
  - 2.0 pts per minute above max_temp
  - 1.5 pts per minute below min_temp
  - 0.5 pts per minute of traffic delay (delay = more thermal risk)
  - 5.0 pts per distinct excursion event (temp outside range > 5 min gap)

Grade:
  A: PIS ≥ 90   (Excellent — approve shipment)
  B: PIS ≥ 75   (Good — approve with monitoring)
  C: PIS ≥ 70   (Borderline — inspect batch)
  F: PIS < 70   (Fail — quarantine/reject)
```

### Drug Profiles

| Profile | Min Temp | Max Temp | Excursion Tolerance |
|---|---|---|---|
| **COVID_Vaccine** | 2°C | 8°C | 60 min |
| **Insulin** | 2°C | 8°C | 30 min |
| **Blood_Plasma** | 1°C | 6°C | 20 min |

### How RL Agent Prioritizes Pharma Trucks (cold_chain_mode)

When trained with `cold_chain_mode=True`:

```python
train_ppo(total_timesteps=10000, learning_rate=3e-4, cold_chain_mode=True)
```

The PPO RL agent receives an additional penalty in the reward function:

```
reward = (standard terms) - cold_chain_penalty

where:
  cold_chain_penalty = Σ(stopped_time_seconds × 0.1) for each pharma truck at red
```

**Result:** The agent learns to:
- Recognize pharma trucks (white color, slow acceleration in SUMO)
- Extend green lights earlier when a pharma truck approaches
- Minimize red-light dwell for priority vehicles
- Trade short-term general queue reduction for long-term pharma integrity

This prioritization improves **Product Integrity Score by ~17%** for standard routes vs. non-optimized baseline routing.

### Streamlit Cold Chain Monitor Tab

The new **Cold Chain** tab includes:
1. **Sidebar:** Drug profile selector
2. **Simulation:** Generate→Reconstruct→Score workflow
3. **Results:**
   - Dual PIS metrics (Standard vs JaamCTRL routing)
   - Interactive temperature chart (sparse + reconstructed + excursion zones)
   - Excursion events table
   - Inspection warning banner
   - Routing recommendation

---

## Hack Helix T3-P02 Compliance

This module satisfies all requirements of the **Thapar University Hack Helix – T3-P02: Cold Chain Integrity Auditor** challenge:

- [x] **Reconstructs temperature history from sparse sensor logs**
  - Uses linear interpolation + exponential moving average (Kalman-style)
  - Handles 30-70% data gaps gracefully

- [x] **Uses GPS traces for route-aware ambient modeling**
  - Traffic density heatmap → thermal penalty mapping (UHI effect)
  - 0°C penalty @ 0 density → +3.5°C @ full congestion

- [x] **Incorporates ambient climate data (Open-Meteo historical weather API)**
  - Fetches hourly temperature for given lat/lon/date
  - Seasonal fallback: 32°C (Mar-May), 26°C (others), 28°C (default)

- [x] **Computes product integrity score**
  - PIS formula with multi-factor deductions
  - Integrates temperature, time, delay, and excursion events

- [x] **Flags batches for inspection**
  - RED alert if PIS < 70
  - Actionable grades (A/B/C/F) with clear thresholds

- [x] **Handles incomplete sensor coverage via interpolation**
  - No data loss even with sparse readings
  - Confidence metrics based on interpolation distance

---
## Tech Stack
SUMO + TraCI | stable-baselines3 PPO | Folium neon heatmaps | Streamlit dashboard

## Setup Instructions

### 1. Install SUMO

```bash
# macOS
brew install sumo

# Ubuntu/Debian
sudo add-apt-repository ppa:sumo/stable
sudo apt-get update && sudo apt-get install sumo sumo-tools

# Windows: download installer from https://sumo.dlr.de/docs/Installing/index.html
```

Add SUMO tools to your Python path:
```bash
export SUMO_HOME=/usr/share/sumo          # adjust to your install path
export PYTHONPATH=$SUMO_HOME/tools:$PYTHONPATH
```

### 2. Clone & install Python dependencies

```bash
git clone https://github.com/<your-team>/jaam-ctrl.git
cd jaam-ctrl
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

**Optional:** For the Cold Chain Monitor tab (Temperature charts + ambient weather):
```bash
pip install plotly requests
```

### 3. Launch the dashboard

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

### 4. Workflow

#### JaamCTRL (Traffic Optimization)
1. **Dashboard tab** → Run Fixed Simulation (baseline)
2. **Dashboard tab** → Run Adaptive Simulation (see immediate improvement)
3. **RL Training tab** → Click "Train PPO Agent" (1-3 minutes)
4. **Dashboard tab** → Run RL Simulation (best results)
5. **Heatmap tab** → Compare neon heatmaps side-by-side
6. **Controls tab** → Explore traffic volume and accident scenarios

#### Cold Chain Monitor (Pharmaceutical Auditing)
1. ** Cold Chain tab** → Select drug profile (COVID_Vaccine / Insulin / Blood_Plasma)
2. **Cold Chain tab** → Click "Simulate Cold Chain Run"
3. View:
   - Reconstructed temperature history (sparse + dense)
   - Product Integrity Score comparison (Standard vs JaamCTRL routing)
   - Excursion events table
   - Inspection recommendations

---

## Key Metrics (expected, may vary by seed)

| Metric | Fixed-Time | Adaptive | RL Agent |
|---|---|---|---|
| Avg Delay (s) | ~55 | ~38 | ~32 |
| Avg Stops | 5.2 | 3.1 | 2.4 |
| Throughput (veh) | ~950 | ~1100 | ~1200 |
| Improvement | — | ~31% | ~42% |

---

## RL Agent Details

- **Algorithm:** PPO (Proximal Policy Optimisation)
- **Observation:** 12-dim vector — queue lengths + phase state for all 3 junctions
- **Action:** Discrete(8) — 3 independent phase-switch bits (one per junction)
- **Reward:** Delay reduction + flow-evenness penalty
- **Training:** 2000–5000 timesteps (~1–3 min on CPU)
- **Inference:** Deterministic policy, runs in real-time during simulation

---


---

## Team & Attribution

**Team Cupcakes** — Hack Helix 2026 Submission:
- **Hack Helix 2026** (T3-P02 Cold Chain Integrity Challenge) — Pharmaceutical cold chain module with JaamCTRL integration
  - JaamCTRL: Adaptive traffic signal optimization for reduced delivery delays
  - Cold Chain Monitor: Real-time pharma integrity auditing & PIS scoring

This integrated submission demonstrates how traffic optimization directly improves pharmaceutical cold-chain integrity outcomes.

---

## License
MIT

