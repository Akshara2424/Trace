# Step-by-Step Testing Guide

## Phase 1: Syntax & Module Validation ✅ COMPLETE

```bash
# Already verified:
✓ Python syntax check: All files pass
✓ SUMO found: C:\Program Files (x86)\Eclipse\Sumo\
✓ Module imports work
✓ Synthetic env functional: obs shape (24,)
```

---

## Phase 2: Live SUMO Testing (DO THIS NEXT)

### Step 1: Start SUMO Server in Background
```bash
# Option A: GUI (easiest for debugging)
cd sumo/
sumo-gui -c config.sumocfg --remote-port 8813

# Option B: Headless (faster)
cd sumo/
sumo -c config.sumocfg --remote-port 8813 --no-gui
```

The SUMO window should show the Delhi corridor with traffic flowing.

### Step 2: Test SUMO Connector
```bash
python -c "
import sys
sys.path.insert(0, 'src')
from sumo_connector import SUMOConnector, SUMOConfig

# Create connector
config = SUMOConfig(port=8813)
connector = SUMOConnector(config)

# Try to connect
if connector.connect():
    print('✓ Connected to SUMO')
    
    # Test data collection
    q_ew, q_ns = connector.get_queue_lengths(0)
    print(f'Junction 0 queues: EW={q_ew:.2f}, NS={q_ns:.2f}')
    
    p_dens, p_wait = connector.get_pharma_density(0)
    print(f'Pharma at J0: density={p_dens:.2f}, wait={p_wait:.2f}')
    
    speed = connector.get_speed_distribution(0)
    cong = connector.get_congestion_level(0)
    print(f'Speed factor: {speed:.2f}, Congestion: {cong:.2f}')
    
    connector.close()
    print('✓ All queries successful!')
else:
    print('✗ Failed to connect to SUMO')
"
```

Expected output:
```
✓ Connected to SUMO
Junction 0 queues: EW=0.45, NS=0.23
Pharma at J0: density=0.12, wait=0.05
Speed factor: 0.68, Congestion: 0.42
✓ All queries successful!
```

### Step 3: Test JaamCtrlEnv_SUMO
```bash
python -c "
import sys
sys.path.insert(0, 'src')
from rl_agent import JaamCtrlEnv_SUMO

# Create environment
env = JaamCtrlEnv_SUMO(cold_chain_mode=True, sumo_port=8813)

# Reset (should auto-connect to SUMO)
obs, info = env.reset()
print(f'✓ Environment reset: obs shape {obs.shape}')

# Verify 32-dim
assert obs.shape == (32,), f'Expected shape (32,), got {obs.shape}'
print(f'✓ Observation shape correct: {obs.shape}')

# Show first junction data
print(f'Junction 0 data: {obs[:10]}')

# Test one step (advances SUMO by 10 seconds)
action = 2  # Phase switch at junction 1
obs, reward, done, truncated, info = env.step(action)
print(f'✓ Step executed: reward={reward:.3f}')

env.close()
print('✓ Environment test complete!')
"
```

Expected output:
```
✓ Environment reset: obs shape (32,)
✓ Observation shape correct: (32,)
Junction 0 data: [0.45 0.23 1.0 0.0 0.5 0.34 0.12 0.05 0.68 0.42]
✓ Step executed: reward=-0.234
✓ Environment test complete!
```

---

## Phase 3: Training Test

### Quick 1000-timestep Training
```bash
python models/train_sumo_ppo.py \
  --timesteps 1000 \
  --cold-chain \
  --verbose 1
```

This will:
- Take ~5-10 minutes
- Show progress every 100 steps
- Save model to `models/ppo_jaam_ctrl_sumo.zip`
- Save metadata to `models/ppo_jaam_ctrl_sumo_metadata.json`

Expected output:
```
======================================================================
Training PPO Agent on Real SUMO
======================================================================
Timesteps: 1000
Cold-chain mode: True
Learning rate: 0.0003
SUMO port: 8813
======================================================================

Creating SUMO environment...
Creating PPO model...

Starting training loop (1000 timesteps)...
  [100/1000] elapsed: 12.3s
  [200/1000] elapsed: 24.7s
  [300/1000] elapsed: 37.1s
  ...
  [1000/1000] elapsed: 125.4s

Saving model to models/ppo_jaam_ctrl_sumo...
✓ Model saved to models/ppo_jaam_ctrl_sumo
✓ Metadata saved to models/ppo_jaam_ctrl_sumo_metadata.json
✓ Training completed in 125.4 seconds
```

### Check Training Results
```bash
python -c "
import json

with open('models/ppo_jaam_ctrl_sumo_metadata.json') as f:
    metadata = json.load(f, indent=2)

print('Training Metadata:')
print(f'  Model Type: {metadata[\"model_type\"]}')
print(f'  Environment: {metadata[\"environment\"]}')
print(f'  Timesteps: {metadata[\"timesteps\"]}')
print(f'  Cold-chain: {metadata[\"cold_chain_mode\"]}')
print(f'  Learning Rate: {metadata[\"learning_rate\"]}')
print(f'  Observation Space: {metadata[\"observation_space\"]}')
print(f'  Training Time: {metadata[\"training_time_seconds\"]:.1f}s')
print(f'  Timestamp: {metadata[\"timestamp\"]}')
"
```

---

## Phase 4: Application Test

### Launch Dashboard
```bash
streamlit run app.py
```

Then:
1. Under "SUMO Live" tab, verify:
   - ✓ Connection status shows "SUMO found"
   - ✓ PPO model loaded status
   - ✓ "Start Live SUMO Simulation" button visible
   - ✓ Feature overview expanders work
   
2. Check visualizations:
   - ✓ Vehicle type pie chart renders
   - ✓ Speed distribution timeline shows data
   - ✓ Congestion heatmaps display per junction
   - ✓ Pharma vehicle alerts section visible
   
3. Verify controls:
   - ✓ Can click start/stop buttons
   - ✓ No JavaScript errors in browser console

---

## Phase 5: Model Comparison

### Compare Synthetic vs SUMO Model

```bash
# Terminal 1: Start SUMO again
cd sumo/
sumo -c config.sumocfg --remote-port 8813 --no-gui

# Terminal 2: Run test comparison
python -c "
import sys, numpy as np
sys.path.insert(0, 'src')

from rl_agent import JaamCtrlEnv, JaamCtrlEnv_SUMO

# Test synthetic (no SUMO needed)
print('=== SYNTHETIC ENVIRONMENT ===')
env_syn = JaamCtrlEnv(cold_chain_mode=True)
obs_syn, _ = env_syn.reset()
print(f'Observation shape: {obs_syn.shape}')
print(f'Sample values: min={obs_syn.min():.2f}, max={obs_syn.max():.2f}, mean={obs_syn.mean():.2f}')

# Test real SUMO
print('\n=== REAL SUMO ENVIRONMENT ===')
env_real = JaamCtrlEnv_SUMO(cold_chain_mode=True, sumo_port=8813)
obs_real, _ = env_real.reset()
print(f'Observation shape: {obs_real.shape}')
print(f'Sample values: min={obs_real.min():.2f}, max={obs_real.max():.2f}, mean={obs_real.mean():.2f}')

# Compare observations
print('\n=== COMPARISON ===')
print(f'Synthetic obs first 10: {obs_syn[:10]}')
print(f'SUMO obs first 10:      {obs_real[:10]}')

env_real.close()
print('\n✓ Comparison complete!')
"
```

Expected differences:
- Synthetic: More uniform distributions, fixed ranges
- SUMO: Variable distributions matching real traffic patterns
- Both: Values in [0,1] range, no NaN/Inf

---

## Phase 6: Full Validation

### Run Complete Testing Suite
```bash
# Terminal 1: SUMO
cd sumo/
sumo -c config.sumocfg --remote-port 8813 --no-gui

# Terminal 2: Tests
python -c "
import sys
sys.path.insert(0, 'src')

print('SUMO Real Integration - Full Validation')
print('=' * 50)

# Test 1: Module imports
print('\n[1/6] Testing module imports...')
try:
    from sumo_connector import SUMOConnector, SUMOConfig
    from rl_agent import JaamCtrlEnv_SUMO
    print('✓ All modules imported')
except Exception as e:
    print(f'✗ Import failed: {e}')
    sys.exit(1)

# Test 2: Connection
print('[2/6] Testing SUMO connection...')
config = SUMOConfig(port=8813)
connector = SUMOConnector(config)
if connector.connect():
    print('✓ Connected to SUMO')
else:
    print('✗ Connection failed')
    sys.exit(1)

# Test 3: Data collection
print('[3/6] Testing data collection...')
for j in range(3):
    q = connector.get_queue_lengths(j)
    p = connector.get_pharma_density(j)
    s = connector.get_speed_distribution(j)
    c = connector.get_congestion_level(j)
    print(f'  J{j}: q={sum(q):.2f}, pharma={p[0]:.2f}, speed={s:.2f}, cong={c:.2f}')
print('✓ Data collection working')

# Test 4: Environment
print('[4/6] Testing JaamCtrlEnv_SUMO...')
env = JaamCtrlEnv_SUMO(cold_chain_mode=True, sumo_port=8813)
obs, _ = env.reset()
assert obs.shape == (32,), f'Shape mismatch: {obs.shape}'
print(f'✓ Environment reset: obs shape {obs.shape}')

# Test 5: Stepping
print('[5/6] Testing environment stepping...')
for i in range(5):
    action = i % 8
    obs, reward, done, _, _ = env.step(action)
    assert obs.shape == (32,), f'Shape mismatch after step'
    assert not np.isnan(reward), f'NaN reward at step {i}'
    assert not np.isnan(obs).any(), f'NaN in obs at step {i}'

print('✓ Environment stepping works (5 steps tested)')
env.close()

# Test 6: Observation ranges
print('[6/6] Testing observation value ranges...')
env = JaamCtrlEnv_SUMO(cold_chain_mode=False, sumo_port=8813)
obs, _ = env.reset()
assert (obs >= 0).all(), f'Negative observations found'
assert (obs <= 1).all(), f'Observations >1 found'
print('✓ All observations in valid range [0,1]')
env.close()

connector.close()

print('\n' + '=' * 50)
print('✓ FULL VALIDATION PASSED - SYSTEM READY')
print('=' * 50)
"
```

---

## Phase 7: Monitoring Setup (Optional)

### Monitor App in Real-Time
```bash
# Terminal 1: SUMO with GUI
cd sumo/
sumo-gui -c config.sumocfg --remote-port 8813

# Terminal 2: Training
python models/train_sumo_ppo.py --timesteps 5000 --cold-chain

# Terminal 3: Dashboard
streamlit run app.py
#  Visit http://localhost:8501 → "SUMO Live" tab
```

This will show:
- SUMO visualization with traffic in real-time
- Terminal showing training progress (episodes, rewards)
- Streamlit dashboard with live metrics updates

---

## Checkpoint Summary

| Phase | Status | Action |
|-------|--------|--------|
| 1. Syntax | ✅ DONE | Already verified |
| 2. SUMO Connection | ⏳ NEXT | Run Step 1-3 above |
| 3. Training | ⏳ NEXT | Run Phase 3 training |
| 4. App | ⏳ NEXT | Launch streamlit |
| 5. Comparison | ⏳ NEXT | Run comparison |
| 6. Full Validation | ⏳ NEXT | Run full suite |

---

## Troubleshooting Commands

If you encounter issues:

```bash
# Check SUMO is running
netstat -an | find "8813"

# Kill stuck SUMO process
taskkill /IM sumo*.exe /F

# Check Python version
python --version

# Verify requirements
pip list | grep -E "(traci|stable-baselines3|gymnasium)"

# Test SUMO installation
sumo --version
```

---

## Success Criteria

You'll know it's working when:

1. ✅ SUMO connector successfully connects and retrieves data
2. ✅ JaamCtrlEnv_SUMO initializes with (32,) observation shape
3. ✅ Training loop completes without errors
4. ✅ Dashboard loads with SUMO Live tab visible
5. ✅ Real vehicle data displays in metrics tables
6. ✅ No NaN/Inf in observations during 50+ steps
7. ✅ Reward signal is continuous and reasonable (-1 to +1 range)

---

## Next: Production Deployment

Once all tests pass:

1. **Scale up training**: Run 50,000 timesteps (5-8 hours)
2. **Validate performance**: Compare vs synthetic baseline
3. **Test cold-chain**: Add pharma vehicles to routes.rou.xml
4. **Deploy to edge**: Package model for real traffic management system

See `INTEGRATION_SUMMARY.md` for full deployment roadmap.
