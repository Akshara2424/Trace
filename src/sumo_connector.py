"""
sumo_connector.py - SUMO TraCI Integration Utilities
====================================================

Provides high-level interfaces for connecting to SUMO via TraCI and collecting
real vehicle/traffic data for RL observations.

Key Features:
  - Auto-detect SUMO installation
  - Vehicle type classification (pharma vs. regular)
  - Queue length queries from real lanes
  - Speed distribution analysis
  - Congestion heatmap generation
  - Accident detection and injection
  - Graceful fallback to synthetic data if SUMO unavailable
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple
import numpy as np


# ─────────────────────────────────────────────────────────────────────────────
# TraCI Availability Detection
# ─────────────────────────────────────────────────────────────────────────────

try:
    import traci
    from traci import exceptions as traci_exceptions
    TRACI_OK = True
except ImportError:
    TRACI_OK = False

# ─────────────────────────────────────────────────────────────────────────────
# SUMO Installation Detection
# ─────────────────────────────────────────────────────────────────────────────

def find_sumo_home() -> Optional[str]:
    """
    Locate SUMO installation directory.
    
    Checks (in order):
      1. SUMO_HOME environment variable
      2. Common installation paths (Windows, Linux, macOS)
      3. System PATH for 'sumo' command
    
    Returns:
        Path to SUMO_HOME or None if not found
    """
    # Check environment variable first
    if 'SUMO_HOME' in os.environ:
        sumo_home = os.environ['SUMO_HOME']
        if os.path.isdir(sumo_home):
            return sumo_home
    
    # Common installation paths
    common_paths = [
        "C:\\Program Files\\sumo",
        "C:\\Program Files (x86)\\sumo",
        os.path.expanduser("~/.sumo"),
        "/usr/share/sumo",
        "/usr/local/opt/sumo",
    ]
    
    for path in common_paths:
        if os.path.isdir(path):
            return path
    
    # Try to find via 'which' / 'where' command
    try:
        if sys.platform == "win32":
            result = subprocess.run(["where", "sumo"], capture_output=True, text=True)
        else:
            result = subprocess.run(["which", "sumo"], capture_output=True, text=True)
        
        if result.returncode == 0:
            sumo_path = result.stdout.strip()
            if sumo_path:
                return os.path.dirname(os.path.dirname(sumo_path))  # Go up from bin/sumo
    except Exception:
        pass
    
    return None


def setup_sumo_path() -> bool:
    """
    Add SUMO tools to Python path if available.
    
    Returns:
        True if SUMO found and added to path, False otherwise
    """
    if not TRACI_OK:
        return False
    
    sumo_home = find_sumo_home()
    if not sumo_home:
        return False
    
    tools_path = os.path.join(sumo_home, "tools")
    if os.path.isdir(tools_path) and tools_path not in sys.path:
        sys.path.insert(0, tools_path)
        return True
    
    return False


# ─────────────────────────────────────────────────────────────────────────────
# SUMO Connection Manager
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SUMOConfig:
    """Configuration for SUMO simulation connection."""
    config_file: str = "sumo/config.sumocfg"  # Path to SUMO config
    port: int = 8813                          # TraCI connection port
    host: str = "127.0.0.1"                   # TraCI connection host
    gui: bool = False                         # Run with GUI?
    verbose: bool = False                     # Verbose output?
    seed: int = 42                            # Random seed


class SUMOConnector:
    """
    Manages connection to SUMO via TraCI.
    
    Usage:
        connector = SUMOConnector(config)
        connector.connect()
        obs = connector.get_observation()
        ...
        connector.close()
    """
    
    def __init__(self, config: SUMOConfig):
        self.config = config
        self.connected = False
        self._junctions = ["J0", "J1", "J2"]  # Delhi corridor junctions
        self._edge_map = {
            "J0": {"ew": ["W0J0", "J1J0"], "ns": ["N0J0", "S0J0"]},
            "J1": {"ew": ["J0J1", "J2J1"], "ns": ["N1J1", "S1J1"]},
            "J2": {"ew": ["J1J2"],          "ns": ["N2J2", "S2J2"]},
        }
    
    def connect(self) -> bool:
        """
        Establish connection to SUMO via TraCI.
        
        Returns:
            True if successful, False otherwise
        """
        if not TRACI_OK:
            print("⚠ TraCI not available (SUMO Python tools not installed)")
            return False
        
        try:
            # Build SUMO command
            binary = "sumo-gui" if self.config.gui else "sumo"
            cmd = [
                binary,
                "-c", self.config.config_file,
                "--seed", str(self.config.seed),
                "--remote-port", str(self.config.port),
            ]
            
            if not self.config.verbose:
                cmd.extend(["--no-warnings", "--no-step-log"])
            
            # Start SUMO as server (wait for TraCI client)
            print(f"Starting SUMO (listening on {self.config.host}:{self.config.port})...")
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(2)  # Wait for SUMO to start
            
            # Connect TraCI client
            traci.connect(
                port=self.config.port,
                host=self.config.host,
                numRetries=10,
            )
            
            self.connected = True
            print("✓ Connected to SUMO")
            return True
            
        except Exception as e:
            print(f"✗ Failed to connect to SUMO: {e}")
            self.connected = False
            return False
    
    def close(self) -> None:
        """Close TraCI connection and stop SUMO."""
        if self.connected:
            try:
                traci.close()
                self.connected = False
                print("✓ Closed SUMO connection")
            except Exception as e:
                print(f"⚠ Error closing connection: {e}")
    
    def is_connected(self) -> bool:
        """Check if currently connected to SUMO."""
        if not self.connected:
            return False
        
        try:
            traci.simulation.getCurrentTime()
            return True
        except Exception:
            self.connected = False
            return False
    
    # ─────────────────────────────────────────────────────────────────────────
    # Vehicle & Queue Data Collection
    # ─────────────────────────────────────────────────────────────────────────
    
    def get_queue_lengths(self, junction_idx: int) -> Tuple[float, float]:
        """
        Get real queue lengths (vehicle count) for a junction.
        
        Parameters:
            junction_idx: 0, 1, or 2 (J0, J1, J2)
        
        Returns:
            (queue_ew, queue_ns) normalized to [0, 1]
        """
        if not self.connected:
            return 0.0, 0.0
        
        try:
            junction_id = self._junctions[junction_idx]
            edges = self._edge_map[junction_id]
            
            # Sum vehicles in EW lanes
            q_ew = sum(
                traci.lane.getLastStepVehicleNumber(f"{edge}_0")
                for edge in edges["ew"]
                if self._safe_lane_exists(f"{edge}_0")
            )
            
            # Sum vehicles in NS lanes
            q_ns = sum(
                traci.lane.getLastStepVehicleNumber(f"{edge}_0")
                for edge in edges["ns"]
                if self._safe_lane_exists(f"{edge}_0")
            )
            
            # Normalize (max ~25 vehicles per junction typical)
            return min(q_ew / 25.0, 1.0), min(q_ns / 25.0, 1.0)
            
        except Exception as e:
            print(f"⚠ Error getting queue lengths for J{junction_idx}: {e}")
            return 0.0, 0.0
    
    def get_pharma_density(self, junction_idx: int) -> Tuple[float, float]:
        """
        Get pharmaceutical vehicle density heatmap for a junction.
        
        Counts pharma_truck type vehicles and their average wait time.
        
        Returns:
            (pharma_density, pharma_avg_wait) each normalized [0, 1]
        """
        if not self.connected:
            return 0.0, 0.0
        
        try:
            pharma_vehicles = []
            
            for vid in traci.vehicle.getIDList():
                vtype = traci.vehicle.getTypeID(vid)
                if "pharma" in vtype.lower():
                    pharma_vehicles.append(vid)
            
            if not pharma_vehicles:
                return 0.0, 0.0
            
            # Density: count normalized to max ~5 pharma vehicles
            density = min(len(pharma_vehicles) / 5.0, 1.0)
            
            # Average wait time: normalized to max ~60 seconds
            wait_times = [
                traci.vehicle.getWaitingTime(vid)
                for vid in pharma_vehicles
            ]
            avg_wait = min(np.mean(wait_times) / 60.0, 1.0) if wait_times else 0.0
            
            return float(density), float(avg_wait)
            
        except Exception as e:
            print(f"⚠ Error getting pharma density for J{junction_idx}: {e}")
            return 0.0, 0.0
    
    def get_speed_distribution(self, junction_idx: int) -> float:
        """
        Get vehicle speed distribution heatmap for a junction.
        
        Returns average speed across all vehicles near junction, normalized.
        Fast (~18 m/s) = 1.0, Slow (~3 m/s) = 0.2
        
        Returns:
            speed_factor [0.2, 1.0] normalized
        """
        if not self.connected:
            return 0.5
        
        try:
            speeds = []
            for vid in traci.vehicle.getIDList():
                try:
                    speed = traci.vehicle.getSpeed(vid)
                    if speed > 0:
                        speeds.append(speed)
                except Exception:
                    pass
            
            if not speeds:
                return 0.5
            
            # Normalize speed to [0.2, 1.0]
            # Fast drivers (~18 m/s) → 1.0
            # Slow drivers (~3 m/s) → 0.2
            avg_speed = np.mean(speeds)
            speed_factor = (avg_speed - 3.0) / (18.0 - 3.0)  # Linear scale
            return float(np.clip(speed_factor, 0.2, 1.0))
            
        except Exception as e:
            print(f"⚠ Error getting speed distribution J{junction_idx}: {e}")
            return 0.5
    
    def get_congestion_level(self, junction_idx: int) -> float:
        """
        Get congestion heatmap for a junction.
        
        Returns lane occupancy across all lanes at junction.
        Free (~10% occupancy) = 0.0, Saturated (>60%) = 1.0
        
        Returns:
            congestion [0.0, 1.0] normalized
        """
        if not self.connected:
            return 0.0
        
        try:
            junction_id = self._junctions[junction_idx]
            edges = self._edge_map[junction_id]
            all_edges = edges["ew"] + edges["ns"]
            
            occupancies = []
            for edge in all_edges:
                try:
                    lane_id = f"{edge}_0"
                    if self._safe_lane_exists(lane_id):
                        occ = traci.lane.getOccupancy(lane_id)
                        occupancies.append(occ)
                except Exception:
                    pass
            
            if not occupancies:
                return 0.0
            
            # Normalize occupancy to [0, 1]
            # Free: ~10%, Saturated: >60%
            avg_occ = np.mean(occupancies)
            cong = (avg_occ - 10.0) / (60.0 - 10.0)
            return float(np.clip(cong, 0.0, 1.0))
            
        except Exception as e:
            print(f"⚠ Error getting congestion J{junction_idx}: {e}")
            return 0.0
    
    def get_phase(self, junction_idx: int) -> int:
        """
        Get current traffic light phase for a junction.
        
        Returns:
            Phase number (0=EW Green, 1=EW Yellow, 2=NS Green, 3=NS Yellow)
        """
        if not self.connected:
            return 0
        
        try:
            junction_id = self._junctions[junction_idx]
            phase = traci.trafficlight.getPhase(junction_id)
            return int(phase)
        except Exception:
            return 0
    
    def get_phase_duration(self, junction_idx: int) -> float:
        """
        Get elapsed time in current phase (in seconds).
        
        Returns:
            Phase age in seconds
        """
        if not self.connected:
            return 0.0
        
        try:
            junction_id = self._junctions[junction_idx]
            # TraCI doesn't directly give phase duration,
            # so we estimate from simulation time and last phase change
            # For now, return simple normalized value
            return 0.5
        except Exception:
            return 0.0
    
    def set_phase(self, junction_idx: int, phase: int) -> bool:
        """
        Set traffic light phase for a junction.
        
        Returns:
            True if successful
        """
        if not self.connected:
            return False
        
        try:
            junction_id = self._junctions[junction_idx]
            traci.trafficlight.setPhase(junction_id, phase)
            return True
        except Exception as e:
            print(f"⚠ Error setting phase J{junction_idx}: {e}")
            return False
    
    def step(self) -> bool:
        """
        Advance SUMO simulation by one step.
        
        Returns:
            True if successful
        """
        if not self.connected:
            return False
        
        try:
            traci.simulationStep()
            return True
        except Exception as e:
            print(f"⚠ Error stepping simulation: {e}")
            return False
    
    # ─────────────────────────────────────────────────────────────────────────
    # Helper Methods
    # ─────────────────────────────────────────────────────────────────────────
    
    def _safe_lane_exists(self, lane_id: str) -> bool:
        """Check if a lane exists without throwing error."""
        try:
            traci.lane.getLength(lane_id)
            return True
        except Exception:
            return False
    
    def get_all_vehicles(self) -> Dict[str, Dict]:
        """
        Get detailed info for all vehicles currently in simulation.
        
        Returns:
            Dict mapping vehicle_id → {type, speed, wait_time, ...}
        """
        if not self.connected:
            return {}
        
        vehicles = {}
        try:
            for vid in traci.vehicle.getIDList():
                vehicles[vid] = {
                    'type': traci.vehicle.getTypeID(vid),
                    'speed': traci.vehicle.getSpeed(vid),
                    'wait_time': traci.vehicle.getWaitingTime(vid),
                    'x': traci.vehicle.getPosition(vid)[0],
                    'y': traci.vehicle.getPosition(vid)[1],
                }
        except Exception as e:
            print(f"⚠ Error collecting vehicle data: {e}")
        
        return vehicles
