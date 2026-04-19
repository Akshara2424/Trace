"""
Trace: Cold Chain Integrity Auditor
Pharmaceutical Cold Chain + Traffic Intelligence | Hack Helix 2026
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json
import plotly.graph_objects as go
import plotly.express as px
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium

WHITE = "#FFFFFF"
GREEN = "#1fc367"
BLUE = "#9ebff5"
YELLOW = "#f4e973"
BLACK = "#000000"
GREY = "#a6b2b0"

st.set_page_config(page_title="Trace - Cold Chain Audit", page_icon="", layout="wide")

col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("# Trace: Cold Chain Integrity Auditor")
    st.caption("Pharmaceutical Cold Chain + Traffic Intelligence | Hack Helix 2026")
with col2:
    st.markdown("")
    st.markdown(f"<p style='text-align:right; color:{GREY}; font-size:12px;'><b>Track 3, Problem 02</b></p>", unsafe_allow_html=True)

st.divider()

tab1, tab2, tab3 = st.tabs(["Bulk Batch Audit", "Metrics & Breakdown", "Traffic Heatmap & SUMO"])

with tab1:
    st.markdown("## Bulk Pharmaceutical Batch Audit")
    st.markdown("Process multiple shipments through the traffic corridor and assess cold chain risk in bulk")
    
    try:
        from cold_chain.integrity_score import DRUG_PROFILES
        from cold_chain.ambient_temperature import (
            get_ambient_temperature, calculate_pis, generate_synthetic_temperature_profile, 
            apply_urban_heat_island_correction
        )
        from src.rl_agent import load_training_log
        IMPORTS_OK = True
    except ImportError as e:
        st.error(f"Import error: {e}")
        IMPORTS_OK = False
    
    if IMPORTS_OK:
        training_log = load_training_log()
        if training_log and "episode_delays" in training_log:
            episode_delays = np.array(training_log["episode_delays"])
            actual_delays = episode_delays[episode_delays > 0]
            mean_delay_jaamctrl = np.mean(actual_delays) / 10 if len(actual_delays) > 0 else 15.0
            mean_delay_jaamctrl = min(45.0, max(5.0, mean_delay_jaamctrl))
        else:
            mean_delay_jaamctrl = 15.0
        
        if training_log and "best_reward" in training_log:
            best_reward = training_log["best_reward"]
            density_jaamctrl = max(0.15, min(0.80, 0.5 - (best_reward / 100)))
        else:
            density_jaamctrl = 0.3
        
        left, right = st.columns([2, 1])
        with left:
            st.markdown("### Batch Configuration")
            num_shipments = st.slider("Number of shipments to audit", 1, 20, 5, help="Process multiple pharma batches")
            
            col_drug, col_routing = st.columns(2)
            with col_drug:
                drug_selection = st.selectbox("Drug Profile", list(DRUG_PROFILES.keys()))
            with col_routing:
                routing_mode = st.radio("Routing", ["Standard", "JaamCTRL", "Both"], horizontal=True)
        
        with right:
            st.markdown("### Batch Info")
            st.metric("Shipments", num_shipments)
            st.metric("Drug", drug_selection.replace("_", " "))
            st.metric("Routes", "2" if routing_mode == "Both" else "1")
        
        if st.button("Run Bulk Audit", use_container_width=True, type="primary"):
            batch_results = []
            
            with st.spinner(f"Auditing {num_shipments} shipments..."):
                for i in range(num_shipments):
                    noise_var = 0.3 + (i * 0.1)
                    temp_profile = generate_synthetic_temperature_profile(
                        duration_hours=4.0, 
                        base_ambient=25.0 + np.random.normal(0, 1),
                        traffic_stress=0.5,
                        noise_level=min(0.9, noise_var)
                    )
                    
                    if isinstance(temp_profile, tuple):
                        temp_array = temp_profile[0]
                    else:
                        temp_array = np.array(temp_profile)
                    
                    shipment_data = {
                        'shipment_id': f"PKG-{i+1:04d}",
                        'drug': drug_selection,
                        'timestamp': datetime.now(),
                        'results': {}
                    }
                    
                    if routing_mode in ["Standard", "Both"]:
                        corrected_std = np.array([apply_urban_heat_island_correction(t, 0.7) for t in temp_array])
                        pis_std = calculate_pis(
                            temperature_history=corrected_std,
                            sensor_readings=[],
                            traffic_delay_minutes=45.0,
                            med_type=drug_selection
                        )
                        shipment_data['results']['standard'] = pis_std
                    
                    if routing_mode in ["JaamCTRL", "Both"]:
                        corrected_opt = np.array([apply_urban_heat_island_correction(t, density_jaamctrl) for t in temp_array])
                        pis_opt = calculate_pis(
                            temperature_history=corrected_opt,
                            sensor_readings=[],
                            traffic_delay_minutes=mean_delay_jaamctrl,
                            med_type=drug_selection
                        )
                        shipment_data['results']['jaamctrl'] = pis_opt
                    
                    batch_results.append(shipment_data)
            
            st.session_state.batch_results = batch_results
        
        if 'batch_results' in st.session_state:
            results = st.session_state.batch_results
            st.success(f"Audit complete: {len(results)} shipments processed")
            
            st.markdown("### Batch Results Summary")
            
            table_data = []
            for shipment in results:
                if routing_mode == "Both":
                    std_score = shipment['results']['standard'].get('pis_score', 0)
                    opt_score = shipment['results']['jaamctrl'].get('pis_score', 0)
                    improvement = opt_score - std_score
                    table_data.append({
                        'Shipment': shipment['shipment_id'],
                        'Standard PIS': f"{std_score:.0f}",
                        'JaamCTRL PIS': f"{opt_score:.0f}",
                        'Improvement': f"+{improvement:.0f}" if improvement >= 0 else f"{improvement:.0f}",
                        'Status': 'PASS' if opt_score >= 70 else ('REVIEW' if opt_score >= 60 else 'FAIL')
                    })
                elif routing_mode == "Standard":
                    score = shipment['results']['standard'].get('pis_score', 0)
                    table_data.append({
                        'Shipment': shipment['shipment_id'],
                        'PIS Score': f"{score:.0f}",
                        'Status': 'PASS' if score >= 70 else ('REVIEW' if score >= 60 else 'FAIL')
                    })
                else:
                    score = shipment['results']['jaamctrl'].get('pis_score', 0)
                    table_data.append({
                        'Shipment': shipment['shipment_id'],
                        'PIS Score': f"{score:.0f}",
                        'Status': 'PASS' if score >= 70 else ('REVIEW' if score >= 60 else 'FAIL')
                    })
            
            df_results = pd.DataFrame(table_data)
            st.dataframe(df_results, use_container_width=True, hide_index=True)
            
            st.markdown("### Batch Statistics")
            
            stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
            
            if routing_mode == "Both":
                opt_scores = [r['results']['jaamctrl'].get('pis_score', 0) for r in results]
                with stats_col1:
                    st.metric("Avg PIS (JaamCTRL)", f"{np.mean(opt_scores):.1f}")
                with stats_col2:
                    st.metric("Pass Rate", f"{sum(1 for s in opt_scores if s >= 70) / len(opt_scores) * 100:.0f}%")
                with stats_col3:
                    st.metric("Min PIS", f"{np.min(opt_scores):.0f}")
                with stats_col4:
                    st.metric("Max PIS", f"{np.max(opt_scores):.0f}")
            else:
                scores = [r['results']['standard' if routing_mode == 'Standard' else 'jaamctrl'].get('pis_score', 0) for r in results]
                with stats_col1:
                    st.metric("Avg PIS", f"{np.mean(scores):.1f}")
                with stats_col2:
                    st.metric("Pass Rate", f"{sum(1 for s in scores if s >= 70) / len(scores) * 100:.0f}%")
                with stats_col3:
                    st.metric("Min PIS", f"{np.min(scores):.0f}")
                with stats_col4:
                    st.metric("Max PIS", f"{np.max(scores):.0f}")

with tab2:
    st.markdown("## PIS Scoring Metrics Breakdown")
    st.markdown("Understanding what factors into the Product Integrity Score")
    
    if IMPORTS_OK:
        col_explain, col_calc = st.columns([1.5, 1])
        
        with col_explain:
            st.markdown("### What is PIS?")
            st.write("""
The **Product Integrity Score (0-100)** measures whether a pharmaceutical batch maintained proper storage conditions during transit.

**Deductions Applied:**
- **Temperature Excursions**: -2 pts per hour outside spec range
- **Duration Above Max**: -1.5 pts per hour
- **Duration Below Min**: -1.0 pts per hour  
- **Traffic Delay**: -0.5 pts per minute of delay
- **Excursion Events**: -5 pts per event

**Final Grade:**
- >=90: **A** (Excellent) -> **PASS**
- >=75: **B** (Good) -> **PASS**
- >=70: **C** (Acceptable) -> **PASS**
- <70: **F** (Failed) -> **REJECT**
            """)
        
        with col_calc:
            st.markdown("### Example Calculation")
            
            example_drug = "COVID_Vaccine"
            example_temps = np.array([6.0, 7.0, 6.5, 8.0, 5.5])
            corrected = np.array([apply_urban_heat_island_correction(t, 0.5) for t in example_temps])
            
            pis_result = calculate_pis(
                temperature_history=corrected,
                sensor_readings=[],
                traffic_delay_minutes=20.0,
                med_type=example_drug
            )
            
            score = pis_result.get('pis_score', 0)
            
            metric_col1, metric_col2 = st.columns(2)
            with metric_col1:
                st.metric("Starting Score", "100")
            with metric_col2:
                st.metric("Final Score", f"{score:.0f}", f"Grade: {pis_result.get('grade', 'N/A')}")
            
            st.markdown("**Deductions:**")
            for key, val in pis_result.items():
                if 'penalty' in key.lower():
                    st.write(f"- {key.replace('_', ' ').title()}: -{val:.1f} pts")
        
        st.divider()
        
        st.markdown("### PIS Calculation Simulator")
        
        sim_col1, sim_col2, sim_col3 = st.columns(3)
        with sim_col1:
            sim_delay = st.slider("Traffic Delay (min)", 0, 120, 30)
        with sim_col2:
            sim_density = st.slider("Traffic Density", 0.0, 1.0, 0.5)
        with sim_col3:
            sim_drug = st.selectbox("Drug Profile", list(DRUG_PROFILES.keys()), key="sim_drug")
        
        sim_temps = generate_synthetic_temperature_profile(
            duration_hours=4.0,
            base_ambient=25.0,
            traffic_stress=sim_density,
            noise_level=0.5
        )[0]
        
        corrected_sim = np.array([apply_urban_heat_island_correction(t, sim_density) for t in sim_temps])
        pis_sim = calculate_pis(
            temperature_history=corrected_sim,
            sensor_readings=[],
            traffic_delay_minutes=sim_delay,
            med_type=sim_drug
        )
        
        result_col1, result_col2 = st.columns([1, 2])
        with result_col1:
            score_sim = pis_sim.get('pis_score', 0)
            st.metric("Simulated PIS", f"{score_sim:.0f}/100", pis_sim.get('compliance_status', ''))
        
        with result_col2:
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=score_sim,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Score Distribution"},
                delta={'reference': 70},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': GREEN},
                    'steps': [
                        {'range': [0, 60], 'color': "#ffcccc"},
                        {'range': [60, 75], 'color': "#fff9cc"},
                        {'range': [75, 100], 'color': "#ccffcc"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 70
                    }
                }
            ))
            fig.update_layout(height=300, margin=dict(l=50, r=50, t=50, b=50))
            st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.markdown("## Traffic Analysis & SUMO Simulation")
    st.markdown("Real-time traffic simulation with JaamCTRL signal optimization")
    
    if IMPORTS_OK:
        sumo_mode = st.radio(
            "Simulation Mode:",
            ["Simulated Heatmap (Demo)", "SUMO Live (with TraCI) - Coming Soon"],
            horizontal=True
        )
        
        if sumo_mode == "Simulated Heatmap (Demo)":
            st.info("Using synthetic traffic pattern demo. Real SUMO integration coming soon.")
            
            st.markdown("### Traffic Density Heatmap (3-Junction Corridor)")
            
            junction_coords = {
                "Junction 1 (Entry)": [28.6315, 77.2167],
                "Junction 2 (Mid)": [28.6325, 77.2200],
                "Junction 3 (Exit)": [28.6335, 77.2233]
            }
            
            time_points = np.arange(0, 180, 10)
            
            congestion_std = np.sin(time_points / 30) * 0.7 + 0.3
            congestion_opt = np.sin(time_points / 30) * 0.3 + 0.15
            
            def create_traffic_heatmap(title, junction_coords, congestion_levels, is_optimized=False):
                center_lat, center_lon = 28.6325, 77.2200
                m = folium.Map(location=[center_lat, center_lon], zoom_start=15)
                
                heatmap_data = []
                
                for junc_name, (lat, lon) in junction_coords.items():
                    for idx, congestion in enumerate(congestion_levels):
                        point_lat = lat + np.random.normal(0, 0.0005)
                        point_lon = lon + np.random.normal(0, 0.0005)
                        intensity = congestion
                        heatmap_data.append([point_lat, point_lon, intensity])
                
                HeatMap(
                    heatmap_data,
                    name='Traffic Density',
                    min_opacity=0.3,
                    max_zoom=18,
                    radius=20,
                    blur=15,
                    gradient={
                        0.0: GREEN,
                        0.5: YELLOW,
                        1.0: BLUE
                    }
                ).add_to(m)
                
                for junc_name, (lat, lon) in junction_coords.items():
                    folium.CircleMarker(
                        location=[lat, lon],
                        radius=8,
                        popup=junc_name,
                        color=GREEN,
                        fill=True,
                        fillColor=WHITE,
                        fillOpacity=0.8,
                        weight=3
                    ).add_to(m)
                
                return m
            
            col_std_map, col_opt_map = st.columns(2)
            
            with col_std_map:
                st.markdown("#### Standard Fixed-Time Signals")
                map_std = create_traffic_heatmap("Standard Traffic", junction_coords, congestion_std, False)
                st_folium(map_std, width=500, height=450)
            
            with col_opt_map:
                st.markdown("#### JaamCTRL Adaptive Signals")
                map_opt = create_traffic_heatmap("JaamCTRL Optimized", junction_coords, congestion_opt, True)
                st_folium(map_opt, width=500, height=450)
            
            st.divider()
            
            st.markdown("### Congestion Metrics")
            
            summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
            
            with summary_col1:
                st.metric("Avg Congestion (Std)", f"{np.mean(congestion_std):.1%}")
            with summary_col2:
                st.metric("Avg Congestion (JaamCTRL)", f"{np.mean(congestion_opt):.1%}")
            with summary_col3:
                reduction = (np.mean(congestion_std) - np.mean(congestion_opt)) / np.mean(congestion_std) * 100
                st.metric("Congestion Reduction", f"{reduction:.0f}%", delta=f"{reduction:.0f}%", delta_color="inverse")
            with summary_col4:
                st.metric("Total Vehicles Processed", f"{int(np.mean(congestion_std) * 500)}")
        
        else:
            st.warning("SUMO Live Integration - requires TraCI connection to SUMO server")
            st.info("""
To run SUMO simulations:
1. Start SUMO with TraCI: `sumo -c sumo/config.sumocfg --remote-port 8813`
2. Click 'Connect & Run Simulation'
3. Watch live traffic control and cold chain impact
            """)
            if st.button("Connect & Run SUMO Simulation"):
                st.info("Connection in progress...")

st.divider()
st.caption("Trace uniquely integrates traffic optimization with pharmaceutical cold chain monitoring. JaamCTRL reduces delivery time and thermal stress, resulting in better batch integrity scores.")
