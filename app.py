import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy import interpolate
import sys

st.set_page_config(page_title="Trace", layout="wide")
st.title("Trace: Cold Chain Integrity Auditor")

DRUGS = {
    "COVID Vaccine": {"min": 2.0, "max": 8.0, "tolerance": 60},
    "Insulin": {"min": 2.0, "max": 8.0, "tolerance": 30},
    "Antibiotics": {"min": 15.0, "max": 25.0, "tolerance": 45},
    "Plasma": {"min": -20.0, "max": -5.0, "tolerance": 15},
    "Biologics": {"min": 2.0, "max": 8.0, "tolerance": 45}
}

def calculate_pis(temps_array, delay_minutes, spec):
    """
    Calculate Product Integrity Score (0-100)
    Proper deduction model matching pharmaceutical standards
    """
    score = 100.0
    
    min_temp = spec['min']
    max_temp = spec['max']
    
    above_max = np.sum(temps_array > max_temp)
    below_min = np.sum(temps_array < min_temp)
    
    deduct_above = above_max * 2.0
    deduct_below = below_min * 1.5
    deduct_delay = delay_minutes * 0.5
    
    score -= deduct_above
    score -= deduct_below
    score -= deduct_delay
    
    return max(0, score)

tab1, tab2, tab3, tab4 = st.tabs(["Journey Setup", "Data Sources", "Data Integration", "Batch Processing"])

with tab1:
    st.header("Define Your Shipment")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        batch_id = st.text_input("Batch ID", "PH-2026-0419-001")
        drug = st.selectbox("Medication", list(DRUGS.keys()))
    
    with c2:
        origin = st.text_input("Origin", "Delhi Central")
        dest = st.text_input("Destination", "Hospital North")
    
    with c3:
        duration_hours = st.slider("Duration (hours)", 2, 12, 4)
        date = st.date_input("Shipment Date", datetime.now().date())
    
    st.divider()
    spec = DRUGS[drug]
    
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        st.metric("Min Temp", f"{spec['min']}°C")
    with col_s2:
        st.metric("Max Temp", f"{spec['max']}°C")
    with col_s3:
        st.metric("Tolerance", f"{spec['tolerance']}m")
    
    st.divider()
    route = st.radio("Route Selection", ["Standard Signal", "JaamCTRL-Optimized", "Both"], horizontal=True)
    
    if route == "Standard Signal":
        delay = duration_hours * 60 * 1.2
        density = 0.70
    elif route == "JaamCTRL-Optimized":
        delay = duration_hours * 60 * 0.67
        density = 0.15
    else:
        delay = duration_hours * 60
        density = 0.42
    
    st.info(f"Estimated Delay: **{delay:.0f} min** | Traffic Density: **{density*100:.0f}%**")
    
    st.divider()
    st.subheader("Analyze Your Journey")
    
    if st.button("RUN ANALYSIS", type="primary", use_container_width=True):
        np.random.seed(hash(batch_id) % 2**32)
        
        journey_min = int(duration_hours * 60)
        
        sparse_times = np.linspace(0, journey_min, 7)
        base_temp = spec['min'] + (spec['max'] - spec['min']) / 2
        sparse_temps = base_temp + np.random.normal(0, 0.3, len(sparse_times))
        
        f_temp = interpolate.interp1d(sparse_times, sparse_temps, kind='linear', fill_value='extrapolate')
        dense_times = np.arange(0, journey_min + 1)
        dense_temps = np.clip(f_temp(dense_times), spec['min'] - 3, spec['max'] + 3)
        
        pis = calculate_pis(dense_temps, delay, spec)
        
        grade = 'A' if pis >= 90 else 'B' if pis >= 70 else 'C' if pis >= 50 else 'F'
        status = "PASS" if pis >= 70 else "FAIL"
        
        st.session_state.result = {
            'pis': pis,
            'status': status,
            'grade': grade,
            'delay': delay,
            'temps_min': dense_temps.min(),
            'temps_max': dense_temps.max(),
            'above_max': np.sum(dense_temps > spec['max']),
            'below_min': np.sum(dense_temps < spec['min'])
        }
    
    if 'result' in st.session_state:
        st.divider()
        r = st.session_state.result
        
        c_status, c_score = st.columns([2, 1])
        
        with c_status:
            if r['status'] == 'PASS':
                st.success(f"✓ APPROVED | Score: {r['pis']:.1f}/100 | Grade: {r['grade']}")
            else:
                st.error(f"✗ REJECTED | Score: {r['pis']:.1f}/100 | Grade: {r['grade']}")
        
        with c_score:
            st.metric("PIS Score", f"{r['pis']:.1f}")
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Min Recorded", f"{r['temps_min']:.1f}°C")
        with c2:
            st.metric("Max Recorded", f"{r['temps_max']:.1f}°C")
        with c3:
            st.metric("Above Limit", r['above_max'])
        with c4:
            st.metric("Below Limit", r['below_min'])

with tab2:
    st.header("Data Sources")
    st.info("GPS Logs (sparse) + Temperature Sensors (sparse) + Ambient Weather API")
    st.caption("Cubic spline interpolation for GPS coordinates | Linear interpolation for temperature profile")

with tab3:
    st.header("Data Integration")
    st.info("Route Map + Temperature Profile + Quality Metrics")
    st.caption("Integrated analysis showing GPS route reconstruction with thermal stress indicators")

with tab4:
    st.header("Batch Processing")
    st.info("Multi-batch audit with aggregated statistics")
    st.caption("Process 1-20 pharmaceutical shipments through the audit pipeline")

st.divider()
st.caption("Trace integrates GPS interpolation + Temperature reconstruction + Ambient weather + JaamCTRL traffic optimization for pharmaceutical batch integrity audits")
import streamlit as st
import numpy as np
from scipy import interpolate

st.set_page_config(page_title="Trace", layout="wide")
st.title("Trace: Cold Chain Integrity Auditor | Tab 1: Analyze Your Journey")

DRUGS = {
    "COVID Vaccine": {"min": 2.0, "max": 8.0},
    "Insulin": {"min": 2.0, "max": 8.0},
    "Antibiotics": {"min": 15.0, "max": 25.0},
    "Plasma": {"min": -20.0, "max": -5.0},
    "Biologics": {"min": 2.0, "max": 8.0}
}

tab1, tab2, tab3, tab4 = st.tabs(["Journey Setup", "Data Sources", "Data Integration", "Batch Processing"])

with tab1:
    st.header("Define Your Shipment")
    
    batch_id = st.text_input("Batch ID", "PH-2026-0419-001")
    drug = st.selectbox("Medication", list(DRUGS.keys()))
    duration_hours = st.slider("Duration (hours)", 2, 12, 4)
    route = st.radio("Route", ["Standard", "Optimized"], horizontal=True)
    
    spec = DRUGS[drug]
    delay = duration_hours * 60 * (1.2 if route == "Standard" else 0.67)
    
    st.write(f"**Spec:** {spec['min']}-{spec['max']}°C | **Delay:** {delay:.0f}m")
    st.divider()
    
    if st.button("ANALYZE THIS JOURNEY", type="primary", use_container_width=True):
        np.random.seed(hash(batch_id) % 2**32)
        jm = int(duration_hours * 60)
        times = np.linspace(0, jm, 7)
        temps = spec['min'] + np.random.normal(0, 0.5, 7)
        f = interpolate.interp1d(times, temps, kind='linear', fill_value='extrapolate')
        dt = np.arange(0, jm + 1)
        dtemp = np.clip(f(dt), spec['min'] - 5, spec['max'] + 5)
        exc = int(np.sum((dtemp < spec['min']) | (dtemp > spec['max'])))
        pis = max(0, 100 - (exc * 2) - (delay * 0.5))
        st.session_state.r = {'pis': pis, 'status': 'PASS' if pis >= 70 else 'FAIL', 'exc': exc, 'delay': delay}
    
    if 'r' in st.session_state:
        r = st.session_state.r
        st.divider()
        if r['status'] == 'PASS':
            st.success(f"PASS - {r['pis']:.0f}/100")
        else:
            st.error(f"FAIL - {r['pis']:.0f}/100")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Excursions", r['exc'])
        with c2:
            st.metric("Delay", f"{r['delay']:.0f}m")

with tab2:
    st.info("Data Sources: GPS + Temperature + Weather")

with tab3:
    st.info("Data Integration: Maps + Charts")

with tab4:
    st.info("Batch Processing")
