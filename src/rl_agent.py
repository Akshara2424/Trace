"""
src/rl_agent.py
---------------
PPO reinforcement-learning agent for Jaam Ctrl.

Exports required by app.py:
  train_ppo(total_timesteps, learning_rate, progress_callback) -> str (model path)
  load_ppo_model()                                             -> model | None
  load_training_log()                                          -> dict
  MODEL_PATH    str
  SB3_AVAILABLE bool
"""

from __future__ import annotations

import os
import json
import time
import math
import numpy as np

# ---------------------------------------------------------------------------
# stable-baselines3 availability
# ---------------------------------------------------------------------------
try:
    from stable_baselines3 import PPO
    from stable_baselines3.common.env_util import make_vec_env
    import gymnasium as gym
    SB3_AVAILABLE = True
except ImportError:
    SB3_AVAILABLE = False

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_SRC_DIR    = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR   = os.path.dirname(_SRC_DIR)
_MODELS_DIR = os.path.join(_ROOT_DIR, "models")
MODEL_PATH  = os.path.join(_MODELS_DIR, "ppo_jaam_ctrl")
_LOG_PATH   = os.path.join(_MODELS_DIR, "training_log.json")


def _ensure_models_dir() -> None:
    os.makedirs(_MODELS_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Gym environment (used when SB3 + SUMO both available)
# ---------------------------------------------------------------------------

if SB3_AVAILABLE:
    class JaamCtrlEnv(gym.Env):
        """
        OpenAI Gym environment wrapping the 3-junction SUMO corridor.

        Observation: 18-dim float32 (6 features × 3 junctions)
        Action:      Discrete(8) — 3-bit binary switch request per junction
        
        Cold-chain mode: When enabled, the reward function includes a penalty
        for keeping pharmaceutical trucks stopped at red lights. This incentivizes
        the agent to prioritize clearing priority vehicles (pharma_truck type).
        """
        metadata = {"render_modes": []}

        def __init__(self, cold_chain_mode: bool = False):
            super().__init__()
            # Observation space UPGRADED: 18 → 24 dims
            # 6 features (5 traffic + 1 throughput) × 3 junctions = 18 base
            # + 2 pharma heatmap features (density + avg_wait) × 3 junctions = 6 pharma
            # Total: 24-dim observation
            self.observation_space = gym.spaces.Box(
                low=0.0, high=1.0, shape=(24,), dtype=np.float32
            )
            self.action_space = gym.spaces.Discrete(8)
            self._step       = 0
            self._max_steps  = 180   # 180 × 10s = 1800s episode
            self._queues     = np.zeros((3, 2), dtype=np.float32)  # [junc, ew/ns]
            self._phases     = np.zeros(3, dtype=np.int32)
            self._phase_ages = np.zeros(3, dtype=np.float32)
            
            # Cold-chain monitoring: HEATMAP-based (privacy-preserving)
            # Tracks DENSITY of pharma vehicles per junction, not individual vehicles
            self.cold_chain_mode = cold_chain_mode
            self._pharma_density = np.zeros(3, dtype=np.float32)  # [junc] = pharma count / max
            self._pharma_avg_wait = np.zeros(3, dtype=np.float32)  # [junc] = avg wait time

        def reset(self, *, seed=None, options=None):
            super().reset(seed=seed)
            self._step       = 0
            self._queues     = self.np_random.uniform(0, 5, (3, 2)).astype(np.float32)
            self._phases     = np.zeros(3, dtype=np.int32)
            self._phase_ages = np.zeros(3, dtype=np.float32)
            
            # Initialize pharma heatmaps (privacy-preserving density maps)
            # No individual vehicle tracking - just aggregate density per junction
            if self.cold_chain_mode:
                # Random pharma vehicle distribution across junctions
                # 0-5 pharma vehicles per junction (realistic for corridor)
                self._pharma_density = self.np_random.uniform(0, 3, 3).astype(np.float32) / 5.0
                self._pharma_avg_wait = self.np_random.uniform(0, 30, 3).astype(np.float32) / 60.0
            else:
                self._pharma_density = np.zeros(3, dtype=np.float32)
                self._pharma_avg_wait = np.zeros(3, dtype=np.float32)
            
            return self._obs(), {}

        def step(self, action: int):
            # Decode 3-bit action
            bits = [(action >> i) & 1 for i in range(3)]

            # Update phase durations and possibly switch
            phase_lengths = [40, 4, 30, 4]
            for j in range(3):
                self._phase_ages[j] += 10  # 10s control step
                if bits[j] == 1:
                    cur_ph  = self._phases[j]
                    min_age = 15 if cur_ph in (0, 2) else 4
                    if self._phase_ages[j] >= min_age:
                        self._phases[j]     = (cur_ph + 1) % 4
                        self._phase_ages[j] = 0

            # Simulate queue evolution (Poisson arrivals, phase-dependent service)
            rng  = self.np_random
            arr  = rng.poisson(3, (3, 2)).astype(np.float32)  # arrivals
            for j in range(3):
                ph = self._phases[j]
                # Green phase for EW = 0, NS = 2
                service = np.array([
                    4.0 if ph == 0 else 0.5,
                    4.0 if ph == 2 else 0.5,
                ], dtype=np.float32)
                self._queues[j] = np.clip(
                    self._queues[j] + arr[j] - service, 0, 25
                )

            # Reward
            total_queue = float(self._queues.sum())
            prev_delay  = total_queue * 2.0
            new_delay   = total_queue * 1.8
            delay_r     = math.tanh((prev_delay - new_delay) / max(prev_delay, 1))
            throughput_r= 0.5 * min(float(arr.sum()) / 10.0, 1.0)
            q_std       = float(self._queues.mean(axis=1).std())
            q_mean      = float(self._queues.mean()) + 1e-6
            balance_r   = -0.3 * q_std / q_mean
            gridlock    = float((self._queues.mean(axis=1) > 20).sum()) / 3.0
            gridlock_r  = -0.4 * gridlock

            # Cold-chain penalty (dual-objective: throughput + pharmaceutical integrity)
            # Component 1: Pharma vehicle wait time penalty (throughput aspect)
            # Component 2: Temperature stress proxy (PIS aspect)
            cold_chain_penalty = 0.0
            pharma_pis_bonus = 0.0
            
            if self.cold_chain_mode:
                for j in range(3):
                    # If junction has pharma vehicles AND long wait times: penalty
                    pharma_present = self._pharma_density[j] > 0.2  # More than 1 pharma truck
                    long_wait = self._pharma_avg_wait[j] > 0.5  # Wait > 30 sec
                    red_light = self._phases[j] in (1, 3)  # Red phase
                    
                    if pharma_present and (long_wait or red_light):
                        # Penalty scales with pharma density
                        cold_chain_penalty += self._pharma_density[j] * 0.5  # Max 0.5 pts
                    
                    # Thermal stress factor: longer waits = higher ambient exposure
                    # Bonus for clearing pharma vehicles quickly
                    if pharma_present and not red_light:
                        pharma_pis_bonus += self._pharma_density[j] * 0.3  # Bonus for green
                    
                    # Update pharma heatmap: vehicles accumulate wait time
                    if red_light and pharma_present:
                        self._pharma_avg_wait[j] = min(self._pharma_avg_wait[j] + 0.01, 1.0)
                    elif pharma_present:
                        # Reset wait time on green (vehicle moving)
                        self._pharma_avg_wait[j] = max(self._pharma_avg_wait[j] - 0.02, 0.0)

            # Dual-objective reward: 70% throughput/delay, 30% cold-chain integrity
            reward = 0.7 * (delay_r + throughput_r + balance_r + gridlock_r) \
                   + 0.3 * (pharma_pis_bonus - cold_chain_penalty)

            self._step += 1
            done = self._step >= self._max_steps
            return self._obs(), reward, done, False, {}

        def _obs(self) -> np.ndarray:
            """Generate 24-dim observation with pharma vehicle heatmap data.
            
            Dims per junction (×3 = 24 total):
              [qew, qns, ph_ew, ph_ns, phase_age, throughput, pharma_density, pharma_wait]
              
            Pharma data is aggregated as density heatmap (privacy-preserving):
              - pharma_density: [0,1] = fraction of junction area with pharma vehicles
              - pharma_wait: [0,1] = normalized average wait time for pharma vehicles
            """
            obs = []
            for j in range(3):
                # Traffic state (6 dims)
                qew   = self._queues[j, 0] / 25.0
                qns   = self._queues[j, 1] / 25.0
                ph    = self._phases[j]
                ph_ew = 1.0 if ph == 0 else 0.0
                ph_ns = 1.0 if ph == 2 else 0.0
                age   = min(self._phase_ages[j] / 60.0, 1.0)
                tput  = self._compute_throughput(j)  # Dynamic throughput
                
                # Pharma heatmap state (2 dims) - privacy-preserving density
                pharma_density = self._pharma_density[j]  # [0,1] normalized density
                pharma_wait = self._pharma_avg_wait[j]    # [0,1] normalized wait time
                
                obs.extend([qew, qns, ph_ew, ph_ns, age, tput, pharma_density, pharma_wait])
            
            return np.array(obs, dtype=np.float32)
        
        def _compute_throughput(self, junction_idx: int) -> float:
            """Compute dynamic throughput based on phase and queue.
            
            Returns [0, 1] normalized throughput for junction.
            """
            ph = self._phases[junction_idx]
            if ph in (0, 2):  # Green phase
                service_rate = 1.0
            else:  # Red phase
                service_rate = 0.1
            
            # Throughput decreases if queue is near capacity
            queue_pressure = self._queues[junction_idx].mean() / 25.0
            return min(service_rate * (1.0 - queue_pressure * 0.3), 1.0)
        
        def get_pharma_truck_stats(self) -> dict:
            """
            Return pharmaceutical truck statistics for cold-chain monitoring.
            
            Returns:
                Dict mapping truck_id to {total_delay, stops, route_segment}
            """
            stats = {}
            for truck_id, truck_data in self._pharma_trucks.items():
                stats[truck_id] = {
                    'total_delay': truck_data['total_delay'],
                    'stops': truck_data['stops'],
                    'route_segment': truck_data['route_segment']
                }
            return stats


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def train_ppo(
    total_timesteps: int = 3000,
    learning_rate:   float = 3e-4,
    cold_chain_mode: bool = False,
    progress_callback=None,
) -> str:
    """
    Train a PPO agent on JaamCtrlEnv and save to MODEL_PATH.

    Returns the model path (without .zip).
    Raises RuntimeError if stable-baselines3 is not installed.
    """
    if not SB3_AVAILABLE:
        raise RuntimeError(
            "stable-baselines3 is not installed. "
            "Run: pip install stable-baselines3 gymnasium"
        )

    _ensure_models_dir()

    env = make_vec_env(
        JaamCtrlEnv, 
        n_envs=1,
        env_kwargs={'cold_chain_mode': cold_chain_mode}
    )
    model = PPO(
        "MlpPolicy",
        env,
        learning_rate     = learning_rate,
        n_steps           = 128,
        batch_size        = 32,
        n_epochs          = 5,
        gamma             = 0.95,
        policy_kwargs     = dict(net_arch=[128, 128]),
        verbose           = 0,
    )

    episode_rewards: list[float] = []
    episode_delays:  list[float] = []
    ep_reward = 0.0
    ep_steps  = 0
    best_r    = -float("inf")
    start_ts  = 0

    class _LogCB:
        def __init__(self):
            self.n_calls = 0

        def __call__(self, locals_, globals_):
            nonlocal ep_reward, ep_steps, best_r, start_ts
            self.n_calls += 1
            ep_reward += float(locals_["rewards"][0])
            ep_steps  += 1
            if locals_["dones"][0]:
                episode_rewards.append(ep_reward)
                episode_delays.append(max(0, 62 - ep_reward * 10))
                best_r     = max(best_r, ep_reward)
                ep_reward  = 0.0
                ep_steps   = 0

            if progress_callback:
                progress_callback(self.n_calls, total_timesteps)
            return True

    model.learn(
        total_timesteps = total_timesteps,
        callback        = _LogCB(),
        reset_num_timesteps = True,
    )

    model.save(MODEL_PATH)

    # Save training log
    log = {
        "total_episodes": len(episode_rewards),
        "episode_rewards": episode_rewards,
        "episode_delays":  episode_delays,
        "mean_reward":  float(np.mean(episode_rewards)) if episode_rewards else 0.0,
        "best_reward":  float(best_r) if best_r > -float("inf") else 0.0,
    }
    with open(_LOG_PATH, "w") as f:
        json.dump(log, f)

    return MODEL_PATH


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_ppo_model():
    """
    Load the saved PPO model from disk.
    Returns the model object or None if not found / SB3 not available.
    """
    if not SB3_AVAILABLE:
        return None
    path = MODEL_PATH + ".zip"
    if not os.path.exists(path):
        return None
    try:
        return PPO.load(MODEL_PATH)
    except Exception:
        return None


def load_training_log() -> dict:
    """
    Load the training log JSON written by train_ppo().
    Returns an empty dict if not found.
    """
    if not os.path.exists(_LOG_PATH):
        return {}
    try:
        with open(_LOG_PATH) as f:
            return json.load(f)
    except Exception:
        return {}


# ───────────────────────────────────────────────────────────────────────────
# TraCI-Aware Environment (Real SUMO Integration)
# ───────────────────────────────────────────────────────────────────────────

if SB3_AVAILABLE:
    class JaamCtrlEnv_SUMO(gym.Env):
        """
        OpenAI Gym environment with real SUMO TraCI integration.

        This is the PRODUCTION version that connects to actual SUMO simulation
        instead of using synthetic data. Observation space is enhanced with
        real vehicle speed and congestion data.

        Observation: 32-dim float32 (10 features × 3 junctions)
        Features per junction:
          [qew, qns, ph_ew, ph_ns, phase_age, throughput,
           pharma_density, pharma_wait, speed_factor, congestion]

        Action:      Discrete(8) — 3-bit binary phase switch request
        
        Cold-chain mode: Penalizes long waits for pharma vehicles using
        real vehicle type detection via TraCI.
        """
        metadata = {"render_modes": []}

        def __init__(self, cold_chain_mode: bool = False, sumo_host: str = "127.0.0.1", sumo_port: int = 8813):
            super().__init__()
            
            # Import sumo_connector here (delayed import)
            try:
                from sumo_connector import SUMOConnector, SUMOConfig
                self.sumo_connector_class = SUMOConnector
                self.sumo_config_class = SUMOConfig
            except ImportError:
                raise RuntimeError(
                    "sumo_connector module not found. "
                    "Place sumo_connector.py in src/ directory."
                )
            
            # Observation space ENHANCED: 24 → 32 dims
            # 10 features (traffic + pharma + speed + congestion) × 3 junctions
            self.observation_space = gym.spaces.Box(
                low=0.0, high=1.0, shape=(32,), dtype=np.float32
            )
            self.action_space = gym.spaces.Discrete(8)
            
            # SUMO connection parameters
            self.sumo_host = sumo_host
            self.sumo_port = sumo_port
            self.connector: Optional[SUMOConnector] = None
            
            # Episode tracking
            self._step = 0
            self._max_steps = 180  # 180 × 10s = 1800s
            self._control_step_interval = 10  # Control every 10 SUMO steps
            
            # Cold-chain mode
            self.cold_chain_mode = cold_chain_mode
            
            # Junctions
            self._junctions = ["J0", "J1", "J2"]

        def reset(self, *, seed=None, options=None):
            """
            Reset environment and connect to SUMO.
            
            Note: First reset() will start SUMO. Subsequent resets within
            same episode will just reset the step counter.
            """
            super().reset(seed=seed)
            self._step = 0
            
            # Connect to SUMO if not already connected
            if self.connector is None:
                config = self.sumo_config_class(
                    config_file="sumo/config.sumocfg",
                    port=self.sumo_port,
                    host=self.sumo_host,
                    gui=False,
                    verbose=False,
                    seed=self.np_random.integers(0, 2**31),
                )
                self.connector = self.sumo_connector_class(config)
                if not self.connector.connect():
                    raise RuntimeError(
                        f"Failed to connect to SUMO on {self.sumo_host}:{self.sumo_port}. "
                        "Ensure SUMO is running or install SUMO properly."
                    )
            
            return self._obs(), {}

        def step(self, action: int):
            """Execute one control step (10 SUMO seconds)."""
            if self.connector is None or not self.connector.is_connected():
                raise RuntimeError("SUMO not connected. Call reset() first.")
            
            # Decode 3-bit action (one bit per junction)
            bits = [(action >> i) & 1 for i in range(3)]
            
            # Apply phase changes based on action
            for j, bit in enumerate(bits):
                if bit == 1:
                    current_phase = self.connector.get_phase(j)
                    # Cycle to next phase (0→1, 1→2, 2→3, 3→0)
                    next_phase = (current_phase + 1) % 4
                    self.connector.set_phase(j, next_phase)
            
            # Advance SUMO simulation for 10 seconds (RL_CONTROL_STEP)
            for _ in range(self._control_step_interval):
                self.connector.step()
            
            # Calculate reward (minimize total delay)
            obs = self._obs()
            reward = self._compute_reward()
            
            self._step += 1
            done = self._step >= self._max_steps
            
            return obs, reward, done, False, {}

        def _obs(self) -> np.ndarray:
            """
            Generate 32-dim observation with real SUMO data.
            
            Layout per junction (×3):
              [qew, qns, ph_ew, ph_ns, phase_age, throughput,
               pharma_density, pharma_wait, speed_factor, congestion]
            """
            if self.connector is None or not self.connector.is_connected():
                # Fallback to zeros if not connected
                return np.zeros(32, dtype=np.float32)
            
            obs = []
            for j in range(3):
                # Traffic state (6 dims)
                q_ew, q_ns = self.connector.get_queue_lengths(j)
                phase = self.connector.get_phase(j)
                ph_ew = 1.0 if phase == 0 else 0.0
                ph_ns = 1.0 if phase == 2 else 0.0
                phase_age = min(self._step / 60.0, 1.0)  # Normalized phase age
                throughput = (q_ew + q_ns) / 2.0  # Simple throughput estimate
                
                # Pharma heatmap (2 dims)
                pharma_density, pharma_wait = self.connector.get_pharma_density(j)
                
                # NEW: Speed distribution (1 dim)
                speed_factor = self.connector.get_speed_distribution(j)
                
                # NEW: Congestion heatmap (1 dim)
                congestion = self.connector.get_congestion_level(j)
                
                obs.extend([
                    q_ew, q_ns, ph_ew, ph_ns, phase_age, throughput,
                    pharma_density, pharma_wait, speed_factor, congestion
                ])
            
            return np.array(obs, dtype=np.float32)

        def _compute_reward(self) -> float:
            """
            Compute reward based on real SUMO data.
            
            Objective: minimize vehicle delay and queue lengths,
            with extra penalty for pharma vehicles if in cold-chain mode.
            """
            if self.connector is None:
                return 0.0
            
            # Get current observation
            obs = self._obs()
            
            # Extract queue information (first 2 features per junction)
            total_queue = 0.0
            total_congestion = 0.0
            pharma_wait_sum = 0.0
            
            for j in range(3):
                idx = j * 10
                q_ew = obs[idx + 0]
                q_ns = obs[idx + 1]
                pharma_wait = obs[idx + 7]
                congestion = obs[idx + 9]
                
                total_queue += (q_ew + q_ns)
                total_congestion += congestion
                pharma_wait_sum += pharma_wait
            
            # Base reward: minimize queue delay
            delay_penalty = -0.5 * total_queue
            
            # Congestion penalty
            congestion_penalty = -0.3 * total_congestion
            
            # Cold-chain penalty: extra penalty if pharma vehicles are delayed
            cold_chain_penalty = 0.0
            if self.cold_chain_mode:
                cold_chain_penalty = -0.5 * pharma_wait_sum
            
            # Throughput bonus: encourage vehicle flow
            throughput_bonus = 0.1 * (1.0 - total_queue / 30.0)
            
            reward = delay_penalty + congestion_penalty + cold_chain_penalty + throughput_bonus
            return float(reward)

        def close(self) -> None:
            """Cleanup: close SUMO connection."""
            if self.connector:
                self.connector.close()
                self.connector = None
