"""
train_sumo_ppo.py - Train PPO agent on real SUMO simulation
===========================================================

This script trains a PPO agent using the JaamCtrlEnv_SUMO environment,
which connects to real SUMO via TraCI instead of using synthetic data.

Usage:
    python models/train_sumo_ppo.py --timesteps 5000 --cold-chain

Requirements:
    - SUMO installed and SUMO_HOME set
    - stable-baselines3 and gymnasium installed
    - models/run_simulation.py existing
"""

import argparse
import os
import sys
import json
import time
from pathlib import Path

# Add src to path
_SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

# Check dependencies
try:
    from stable_baselines3 import PPO
    from stable_baselines3.common.env_util import make_vec_env
    import gymnasium as gym
    SB3_OK = True
except ImportError:
    SB3_OK = False
    print("⚠ stable-baselines3 not installed. Run: pip install stable-baselines3 gymnasium")

from rl_agent import JaamCtrlEnv_SUMO


def train_sumo_ppo(
    timesteps: int = 5000,
    cold_chain_mode: bool = False,
    learning_rate: float = 3e-4,
    sumo_port: int = 8813,
    verbose: int = 1,
) -> str:
    """
    Train PPO agent on real SUMO simulation.
    
    Args:
        timesteps: Total training timesteps
        cold_chain_mode: Enable pharmaceutical vehicle prioritization
        learning_rate: PPO learning rate
        sumo_port: TraCI port for SUMO connection
        verbose: Verbosity level
    
    Returns:
        Path to saved model
    """
    if not SB3_OK:
        raise RuntimeError(
            "stable-baselines3 not installed. "
            "Run: pip install stable-baselines3[extra] gymnasium"
        )
    
    print(f"\n{'='*70}")
    print(f"Training PPO Agent on Real SUMO")
    print(f"{'='*70}")
    print(f"Timesteps: {timesteps}")
    print(f"Cold-chain mode: {cold_chain_mode}")
    print(f"Learning rate: {learning_rate}")
    print(f"SUMO port: {sumo_port}")
    print(f"{'='*70}\n")
    
    # Create environment
    print("Creating SUMO environment...")
    env = make_vec_env(
        JaamCtrlEnv_SUMO,
        n_envs=1,
        env_kwargs={
            'cold_chain_mode': cold_chain_mode,
            'sumo_port': sumo_port,
        }
    )
    
    # Create PPO model
    print("Creating PPO model...")
    model = PPO(
        "MlpPolicy",
        env,
        learning_rate=learning_rate,
        n_steps=128,
        batch_size=32,
        n_epochs=5,
        gamma=0.95,
        policy_kwargs=dict(net_arch=[256, 256]),
        verbose=verbose,
        tensorboard_log="models/tb_logs",
    )
    
    # Training callbacks
    episode_rewards = []
    best_reward = -float("inf")
    start_time = time.time()
    
    class TrainingCallback:
        def __init__(self):
            self.n_calls = 0
        
        def __call__(self, locals_, globals_):
            nonlocal best_reward
            self.n_calls += 1
            
            # Log progress every 100 calls
            if self.n_calls % 100 == 0:
                elapsed = time.time() - start_time
                print(f"  [{self.n_calls}/{timesteps}] elapsed: {elapsed:.1f}s")
            
            return True
    
    # Train
    print(f"\nStarting training loop ({timesteps} timesteps)...")
    try:
        model.learn(
            total_timesteps=timesteps,
            callback=TrainingCallback(),
            reset_num_timesteps=True,
        )
    except KeyboardInterrupt:
        print("\n⚠ Training interrupted by user")
    except Exception as e:
        print(f"\n✗ Training failed: {e}")
        raise
    finally:
        env.close()
    
    # Save model
    model_dir = Path(__file__).parent
    model_path = model_dir / "ppo_jaam_ctrl_sumo"
    
    print(f"\nSaving model to {model_path}...")
    model.save(str(model_path))
    
    # Save training metadata
    metadata = {
        "model_type": "PPO",
        "environment": "JaamCtrlEnv_SUMO (Real SUMO)",
        "timesteps": timesteps,
        "cold_chain_mode": cold_chain_mode,
        "learning_rate": learning_rate,
        "observation_space": "32-dim (10 features × 3 junctions)",
        "observation_features": [
            "queue_ew", "queue_ns", "phase_ew", "phase_ns",
            "phase_age", "throughput",
            "pharma_density", "pharma_wait",
            "speed_factor", "congestion"
        ],
        "training_time_seconds": time.time() - start_time,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    
    metadata_path = model_dir / "ppo_jaam_ctrl_sumo_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✓ Model saved to {model_path}")
    print(f"✓ Metadata saved to {metadata_path}")
    print(f"✓ Training completed in {time.time() - start_time:.1f} seconds\n")
    
    return str(model_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Train PPO agent on real SUMO simulation"
    )
    parser.add_argument(
        "--timesteps", type=int, default=5000,
        help="Total training timesteps (default: 5000)"
    )
    parser.add_argument(
        "--cold-chain", action="store_true",
        help="Enable cold-chain mode (pharma vehicle prioritization)"
    )
    parser.add_argument(
        "--learning-rate", type=float, default=3e-4,
        help="PPO learning rate (default: 3e-4)"
    )
    parser.add_argument(
        "--sumo-port", type=int, default=8813,
        help="TraCI port for SUMO (default: 8813)"
    )
    parser.add_argument(
        "--verbose", type=int, default=1,
        help="Verbosity level 0-2 (default: 1)"
    )
    
    args = parser.parse_args()
    
    try:
        train_sumo_ppo(
            timesteps=args.timesteps,
            cold_chain_mode=args.cold_chain,
            learning_rate=args.learning_rate,
            sumo_port=args.sumo_port,
            verbose=args.verbose,
        )
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
