"""
cold_chain — Pharmaceutical cold-chain monitoring and routing optimization

Modules:
  - temperature_reconstructor: Sparse sensor log generation and temperature interpolation
  - ambient_overlay: Urban heat island modeling and ambient temperature fetching
  - integrity_score: Product Integrity Score (PIS) computation and routing comparison
  - dataset_loader: Kaggle dataset integration (Delhi Traffic, Delivery Logistics)
"""

from cold_chain.temperature_reconstructor import (
    generate_sparse_sensor_logs,
    reconstruct_temperature_history,
)
from cold_chain.ambient_overlay import (
    traffic_density_to_thermal_penalty,
    fetch_ambient_temperature,
)
from cold_chain.integrity_score import (
    compute_product_integrity_score,
    compare_routing_scenarios,
    compute_time_above_threshold,
    DRUG_PROFILES,
)
from cold_chain.dataset_loader import (
    load_delivery_logistics_sample,
    load_delhi_traffic_sample,
    create_realistic_route,
    extract_route_from_delivery,
    extract_delay_from_traffic,
    extract_weather_from_delivery,
    weather_to_thermal_penalty,
    standardize_vaccine_columns,
    load_vaccine_distribution_logs,
    extract_multihop_journey,
    calculate_cumulative_pis_degradation,
)
from cold_chain.ambient_temperature import (
    get_ambient_temperature,
    apply_urban_heat_island_correction,
    interpolate_sparse_sensors,
    calculate_pis,
    generate_synthetic_temperature_profile,
    analyze_shipment_batch,
    THRESHOLDS,
)

__all__ = [
    'generate_sparse_sensor_logs',
    'reconstruct_temperature_history',
    'traffic_density_to_thermal_penalty',
    'fetch_ambient_temperature',
    'compute_product_integrity_score',
    'compare_routing_scenarios',
    'compute_time_above_threshold',
    'DRUG_PROFILES',
    'load_delivery_logistics_sample',
    'load_delhi_traffic_sample',
    'create_realistic_route',
    'extract_route_from_delivery',
    'extract_delay_from_traffic',
    'extract_weather_from_delivery',
    'weather_to_thermal_penalty',
    'standardize_vaccine_columns',
    'load_vaccine_distribution_logs',
    'extract_multihop_journey',
    'calculate_cumulative_pis_degradation',
    # New ambient_temperature module exports
    'get_ambient_temperature',
    'apply_urban_heat_island_correction',
    'interpolate_sparse_sensors',
    'calculate_pis',
    'generate_synthetic_temperature_profile',
    'analyze_shipment_batch',
    'THRESHOLDS',
]
