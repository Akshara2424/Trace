"""
SUMO Integration Testing Guide
==============================

This document outlines how to test and validate the new SUMO real-time integration.

## Prerequisites

1. SUMO Installation
   ```bash
   # Windows
   choco install sumo
   # OR download from: https://sumo.dlr.de/docs/Downloads.php
   
   # Add SUMO_HOME environment variable
   set SUMO_HOME=C:\Program Files\sumo
   # Add to PYTHONPATH
   set PYTHONPATH=%SUMO_HOME%\tools;%PYTHONPATH%
   ```

2. Python Dependencies (Already installed)
   ```bash
   pip install traci stable-baselines3 gymnasium
   ```

## Testing Progression

### 1. SUMO Connector Module Test
```python
# Test basic SUMO setup detection
from src.sumo_connector import find_sumo_home, setup_sumo_path

sumo_home = find_sumo_home()
print(f"SUMO found at: {sumo_home}")

sumo_path_ok = setup_sumo_path()
print(f"SUMO path setup: {sumo_path_ok}")
```

### 2. Environment Creation Test
```python
# Test JaamCtrlEnv_SUMO can be instantiated
from src.rl_agent import JaamCtrlEnv_SUMO

env = JaamCtrlEnv_SUMO(cold_chain_mode=True)
print(f"Observation space: {env.observation_space.shape}")  # Should be (32,)
print(f"Action space: {env.action_space}")  # Should be Discrete(8)
```

### 3. SUMO Connection Test (Requires SUMO running)
```python
# IMPORTANT: Start SUMO first in server mode
# In a separate terminal:
# sumo -c sumo/config.sumocfg --remote-port 8813

from src.rl_agent import JaamCtrlEnv_SUMO

env = JaamCtrlEnv_SUMO(cold_chain_mode=True, sumo_port=8813)
try:
    obs, _ = env.reset()
    print(f"Observation shape: {obs.shape}")
    print(f"Sample observation:\n{obs[:10]}")  # First junction data
    
    # Test one step
    action = 2  # EW green switch at J1
    obs, reward, done, truncated, info = env.step(action)
    print(f"Reward: {reward:.3f}")
    
    env.close()
except Exception as e:
    print(f"Error: {e}")
```

### 4. Training Test (Short run)
```bash
# Start SUMO in server mode first
python models/train_sumo_ppo.py --timesteps 500 --cold-chain --verbose 1
```

### 5. App Test
```bash
# Ensure SUMO is either running or gracefully stops
streamlit run app.py
# Navigate to "SUMO Live" tab
```

## Observation Space Validation

The new 32-dim observation space should have this structure:

```
Junction 0 (dims 0-9):
  [queue_ew, queue_ns, phase_ew, phase_ns, phase_age, throughput,
   pharma_density, pharma_wait, speed_factor, congestion]

Junction 1 (dims 10-19):
  [same 10 features]

Junction 2 (dims 20-29):
  [same 10 features]

Expected ranges:
  - queue_*: [0, 1] (normalized by 25)
  - phase_*: {0.0, 1.0} (binary)
  - phase_age: [0, 1] (normalized by 60s)
  - throughput: [0, 1] (queue average)
  - pharma_density: [0, 1]
  - pharma_wait: [0, 1] (normalized by 60s)
  - speed_factor: [0.2, 1.0] (fast/slow)
  - congestion: [0, 1] (lane occupancy)
```

## Troubleshooting

### Issue: "TraCI not available"
**Cause**: SUMO Python tools not in path
**Solution**:
```bash
# Set SUMO_HOME
export SUMO_HOME=/path/to/sumo
# Add tools to Python path
export PYTHONPATH=$SUMO_HOME/tools:$PYTHONPATH
```

### Issue: "Failed to connect to SUMO"
**Cause**: SUMO not running or wrong port
**Solution**:
```bash
# In separate terminal, start SUMO as server
sumo -c sumo/config.sumocfg --remote-port 8813
```

### Issue: "Lane does not exist"
**Cause**: SUMO network edges don't match JUNCTION_EDGES in sumo_connector.py
**Solution**: Update JUNCTION_EDGES mapping to match your network.net.xml

### Issue: "Vehicle type not found"
**Cause**: "pharma_truck" type not in routes.rou.xml
**Solution**: Ensure routes.rou.xml has:
```xml
<vType id="pharma_truck" ... />
<route id="..." edges="...">
  <vehicle type="pharma_truck" id="..." depart="..."/>
</route>
```

## Performance Benchmarks

Expected timing (on Dell i5 machine):
- Environment reset: < 2s
- One step (10 SUMO steps): 2-5ms
- 100 environment steps: ~500ms
- Training 5000 timesteps: 30-60min (depends on CPU)

Expected reward convergence:
- Random agent: reward ~ -50 to 0
- Trained agent: reward ~ +20 to +50
- With cold-chain: slight variance due to pharma prioritization

## Feature Validation Checks

✓ Queue lengths match actual vehicle counts
✓ Pharma vehicles correctly identified by type
✓ Speed values in realistic range (3-18 m/s)
✓ Congestion matches lane occupancy % in SUMO
✓ Phase switches respected (min/max duration)
✓ PPO model can process 32-dim observations
✓ Reward signal is continuous and differentiable
✓ No numerical errors (NaN, Inf) in observations

## Next Steps

1. **Real SUMO Validation**: Run 1800s episode with traffic_scale=1.5, verify metrics
2. **Model Comparison**: Train synthetic vs SUMO model, compare convergence
3. **Cold-Chain Testing**: Add pharma vehicles, verify delay penalties
4. **Deployment**: Package for production use with monitoring

## Architecture Diagram

```
SUMO Simulation (TraCI Server)
         ↓
   sumo_connector.py (SUMOConnector)
     - TraCI queries
     - Data aggregation
         ↓
   JaamCtrlEnv_SUMO (gym.Env)
     - 32-dim observations
     - Gym interface
     - Reward calculation
         ↓
   PPO Agent (stable-baselines3)
     - Policy training
     - Action selection
         ↓
   Streamlit App (SUMO Live Tab)
     - Real-time metrics
     - Vehicle tracking
     - Performance charts
```

## API Reference

### SUMOConnector Methods

```python
connector.connect() → bool
  # Connect to SUMO via TraCI
  
connector.get_queue_lengths(junction_idx: int) → Tuple[float, float]
  # Returns (queue_ew, queue_ns) normalized [0,1]
  
connector.get_pharma_density(junction_idx: int) → Tuple[float, float]
  # Returns (pharma_density, pharma_avg_wait) [0,1]
  
connector.get_speed_distribution(junction_idx: int) → float
  # Returns speed_factor [0.2,1.0]
  
connector.get_congestion_level(junction_idx: int) → float
  # Returns congestion [0,1]
  
connector.set_phase(junction_idx: int, phase: int) → bool
  # Set traffic light phase (0-3)
  
connector.step() → bool
  # Advance simulation 1 second
  
connector.close() → None
  # Cleanup and exit
```

### JaamCtrlEnv_SUMO Methods

```python
env = JaamCtrlEnv_SUMO(cold_chain_mode, sumo_host, sumo_port)
obs, info = env.reset()
obs, reward, done, truncated, info = env.step(action)
env.close()
```

## File Summary

| File | Lines | Purpose |
|------|-------|---------|
| src/sumo_connector.py | 350+ | TraCI connection & data collection |
| src/rl_agent.py | +400 | JaamCtrlEnv_SUMO class added |
| models/train_sumo_ppo.py | 180+ | Training script for SUMO |
| app.py | +400 | SUMO Live Monitor tab |

Total new code: ~1330 lines
"""
