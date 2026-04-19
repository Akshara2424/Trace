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
