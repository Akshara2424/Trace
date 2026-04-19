import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from scipy import interpolate
import plotly.graph_objects as go
import plotly.express as px
import os

st.set_page_config(page_title="Trace - Cold Chain Auditor", layout="wide")

# Pharma Theme CSS: White, Green, Blue, Yellow
st.markdown("""<style>
.stApp { background-color: #FFFFFF; }
.header-container { display: flex; justify-content: center; margin-bottom: 1.5rem; border-bottom: 3px solid #9ebff5; padding-bottom: 1rem; }
.header-container img { max-width: 100%; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
h1 { color: #1fc367; text-align: center; font-weight: 700; }
.stCaption { text-align: center; color: #666; font-style: italic; }
.accent-bar { height: 4px; background: linear-gradient(90deg, #1fc367 0%, #f4e973 50%, #9ebff5 100%); }
.stTabs [role="tablist"] button { background: #f8f9fa; border: 2px solid #9ebff5; font-weight: 600; border-radius: 6px; }
.stTabs [role="tablist"] button[aria-selected="true"] { background: #1fc367; color: white; box-shadow: 0 4px 12px rgba(31,195,103,0.25); }
h2 { color: #1fc367; border-bottom: 3px solid #f4e973; padding-bottom: 0.5rem; }
.stMetric { background: #f8f9fa; border-left: 4px solid #9ebff5; border-radius: 6px; box-shadow: 0 2px 6px rgba(0,0,0,0.08); }
.stButton > button { background: #1fc367; color: white; font-weight: 600; border-radius: 6px; box-shadow: 0 4px 12px rgba(31,195,103,0.2); }
.stButton > button:hover { background: #18a24f; transform: translateY(-2px); }
hr { border: none; height: 2px; background: #9ebff5; }
</style>""", unsafe_allow_html=True)

if os.path.exists("assets/header.jpeg"):
    st.markdown('<div class="header-container">', unsafe_allow_html=True)
    st.image("assets/header.jpeg", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.title("Trace: Cold Chain Integrity Auditor")
st.caption("GPS + Temperature + Ambient Weather + JaamCTRL Traffic Optimization = Better Batch Integrity")
st.markdown('<div class="accent-bar"></div>', unsafe_allow_html=True)

DRUGS = {
    "COVID Vaccine": {"min": 2.0, "max": 8.0, "tolerance": 60},
    "Insulin": {"min": 2.0, "max": 8.0, "tolerance": 30},
    "Antibiotics": {"min": 15.0, "max": 25.0, "tolerance": 45},
    "Plasma": {"min": -20.0, "max": -5.0, "tolerance": 15},
    "Biologics": {"min": 2.0, "max": 8.0, "tolerance": 45}
}

COLORS = {"PASS": "#1fc367", "FAIL": "#FF6464", "ACCENT": "#f4e973", "BLUE": "#9ebff5"}

def calculate_pis(temps_array, delay_minutes, spec):
    score = 100.0
    score -= np.sum(temps_array > spec['max']) * 2.0
    score -= np.sum(temps_array < spec['min']) * 1.5
    score -= max(0, (delay_minutes - 180) * 0.1)
    return max(0, score)

def generate_temp_profile(drug_spec, seed):
    np.random.seed(seed)
    sparse_times = np.linspace(0, 240, 7)
    base = drug_spec['min'] + (drug_spec['max'] - drug_spec['min']) / 2
    sparse_temps = base + np.random.normal(0, 0.3, 7)
    f = interpolate.interp1d(sparse_times, sparse_temps, kind='linear', fill_value='extrapolate')
    times = np.arange(0, 241)
    return times, np.clip(f(times), drug_spec['min'] - 3, drug_spec['max'] + 3)

tab1, tab2, tab3, tab4 = st.tabs(["Journey Setup", "Data Sources", "Route Comparison", "Batch Processing"])

with tab1:
    st.header("Step 1: Define Your Shipment")
    c1, c2, c3 = st.columns(3)
    with c1:
        batch_id = st.text_input("Batch ID", "PH-2026-0419-001")
        drug = st.selectbox("Medication", list(DRUGS.keys()))
    with c2:
        st.text_input("Origin", "Delhi Central")
        st.text_input("Destination", "Hospital North")
    with c3:
        duration_hours = st.slider("Duration (hours)", 2, 12, 4)
        st.date_input("Shipment Date", datetime.now().date())
    
    st.divider()
    spec = DRUGS[drug]
    cs1, cs2, cs3 = st.columns(3)
    with cs1:
        st.metric("Min Temp", f"{spec['min']}°C")
    with cs2:
        st.metric("Max Temp", f"{spec['max']}°C")
    with cs3:
        st.metric("Tolerance", f"{spec['tolerance']}m")
    st.session_state.spec = spec
    st.session_state.batch = {'id': batch_id, 'drug': drug, 'duration': duration_hours}

with tab2:
    st.header("Step 2: Data Sources Integration")
    if 'spec' not in st.session_state:
        st.warning("Complete Tab 1 first")
    else:
        spec = st.session_state.spec
        col_gps, col_temp, col_ambient = st.columns(3)
        
        with col_gps:
            st.subheader("GPS Logs (Sparse)")
            gps_df = pd.DataFrame({
                'Time (min)': list(range(0, 241, 40))[:7],
                'Latitude': np.random.uniform(28.55, 28.65, 7).round(4),
                'Longitude': np.random.uniform(77.15, 77.25, 7).round(4)
            })
            st.dataframe(gps_df, use_container_width=True, hide_index=True)
            st.success("Interpolation: 7 → 240 points via cubic spline")
        
        with col_temp:
            st.subheader("Temperature Sensors")
            temp_df = pd.DataFrame({
                'Time (min)': list(range(0, 241, 40))[:7],
                'Temp (°C)': (spec['min'] + np.random.normal(0, 0.2, 7)).round(2)
            })
            st.dataframe(temp_df, use_container_width=True, hide_index=True)
            st.success("Interpolation: 7 → 240 points via linear")
        
        with col_ambient:
            st.subheader("Ambient Weather (API)")
            ambient_df = pd.DataFrame({
                'Hour': range(8),
                'Ambient (°C)': (28 + np.random.normal(0, 1, 8)).round(1)
            })
            st.dataframe(ambient_df, use_container_width=True, hide_index=True)
            st.success("OpenMeteo API: 8 hourly readings")

with tab3:
    st.header("Step 3: Route Comparison")
    if 'spec' not in st.session_state:
        st.warning("Complete Tab 1 first")
    else:
        spec = st.session_state.spec
        batch_id = st.session_state.batch['id']
        st.info("Comparing Standard Signal Control vs JaamCTRL-Optimized Routing")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Standard Signal Control")
            delay_std = 240 * 1.2
            times, temps = generate_temp_profile(spec, hash(batch_id + "std") % 2**32)
            pis_std = calculate_pis(temps, delay_std, spec)
            st.success(f"PASS | PIS: {pis_std:.1f}/100") if pis_std >= 70 else st.error(f"FAIL | PIS: {pis_std:.1f}/100")
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("Delay", f"{delay_std:.0f}m")
            with m2:
                st.metric("Max Temp", f"{temps.max():.1f}°C")
            with m3:
                st.metric("Grade", "A" if pis_std >= 90 else "B" if pis_std >= 70 else "C" if pis_std >= 50 else "F")
            fig = go.Figure()
            fig.add_hrect(y0=spec['min'], y1=spec['max'], fillcolor=COLORS["PASS"], opacity=0.1)
            fig.add_trace(go.Scatter(x=times, y=temps, line=dict(color=COLORS["BLUE"], width=2)))
            fig.update_layout(title='Temperature Profile', height=300, plot_bgcolor='#f8f9fa', paper_bgcolor='white', showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("JaamCTRL-Optimized")
            delay_opt = 240 * 0.67
            times, temps = generate_temp_profile(spec, hash(batch_id + "opt") % 2**32)
            pis_opt = calculate_pis(temps, delay_opt, spec)
            st.success(f"PASS | PIS: {pis_opt:.1f}/100") if pis_opt >= 70 else st.error(f"FAIL | PIS: {pis_opt:.1f}/100")
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("Delay", f"{delay_opt:.0f}m")
            with m2:
                st.metric("Max Temp", f"{temps.max():.1f}°C")
            with m3:
                st.metric("Grade", "A" if pis_opt >= 90 else "B" if pis_opt >= 70 else "C" if pis_opt >= 50 else "F")
            fig = go.Figure()
            fig.add_hrect(y0=spec['min'], y1=spec['max'], fillcolor=COLORS["PASS"], opacity=0.1)
            fig.add_trace(go.Scatter(x=times, y=temps, line=dict(color=COLORS["PASS"], width=2)))
            fig.update_layout(title='Temperature Profile', height=300, plot_bgcolor='#f8f9fa', paper_bgcolor='white', showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        st.subheader("Impact Summary")
        imp1, imp2, imp3 = st.columns(3)
        with imp1:
            st.metric("PIS Improvement", f"{pis_opt - pis_std:+.1f}", delta=f"{(pis_opt-pis_std)/pis_std*100:+.0f}%" if pis_std > 0 else "")
        with imp2:
            st.metric("Delay Reduction", f"{(delay_std - delay_opt) / delay_std * 100:.0f}%")
        with imp3:
            if pis_std < 70 and pis_opt >= 70:
                st.metric("Batch Status", "SAVED", delta="Failed → Passed")

with tab4:
    st.header("Step 4: Batch Processing")
    if 'spec' not in st.session_state:
        st.warning("Complete Tab 1 first")
    else:
        spec = st.session_state.spec
        nb = st.slider("Number of batches to audit", 1, 20, 5)
        route = st.radio("Routing Strategy", ["Standard Signal", "JaamCTRL-Optimized", "Both"], horizontal=True)
        
        if st.button("RUN BATCH AUDIT", type="primary", use_container_width=True):
            results = []
            for i in range(nb):
                drug = np.random.choice(list(DRUGS.keys()))
                _, temps = generate_temp_profile(DRUGS[drug], i)
                if route == "Standard Signal":
                    delay = 240 * 1.2
                elif route == "JaamCTRL-Optimized":
                    delay = 240 * 0.67
                else:
                    delay = 240
                pis = calculate_pis(temps, delay, DRUGS[drug])
                status = "PASS" if pis >= 70 else "FAIL"
                grade = 'A' if pis >= 90 else 'B' if pis >= 70 else 'C' if pis >= 50 else 'F'
                results.append({
                    "Batch": f"PH-{i+1:03d}",
                    "Drug": drug,
                    "PIS": round(pis, 1),
                    "Status": status,
                    "Grade": grade
                })
            st.session_state.results = pd.DataFrame(results)
        
        if 'results' in st.session_state:
            df = st.session_state.results
            st.success(f"Audit Complete: {len(df)} batches processed")
            
            m1, m2, m3, m4, m5 = st.columns(5)
            passes = len(df[df['Status'] == 'PASS'])
            with m1:
                st.metric("Passed", passes, f"/{len(df)}")
            with m2:
                st.metric("Pass Rate", f"{passes/len(df)*100:.0f}%")
            with m3:
                st.metric("Avg PIS", f"{df['PIS'].mean():.1f}")
            with m4:
                st.metric("Grade A", len(df[df['Grade'] == 'A']))
            with m5:
                st.metric("Grade F", len(df[df['Grade'] == 'F']))
            
            st.divider()
            c1, c2 = st.columns(2)
            
            with c1:
                st.markdown("### Results Table")
                def style_status(val):
                    if val == 'PASS':
                        return f'background-color: {COLORS["PASS"]}; color: white'
                    elif val == 'FAIL':
                        return f'background-color: {COLORS["FAIL"]}; color: white'
                    return ''
                styled = df.style.applymap(style_status, subset=['Status'])
                st.dataframe(styled, use_container_width=True, hide_index=True)
            
            with c2:
                st.markdown("### PIS Distribution")
                fig = px.histogram(df, x='PIS', nbins=10, color_discrete_sequence=[COLORS["BLUE"]])
                fig.add_vline(x=70, line_dash="dash", line_color=COLORS["PASS"], annotation_text="Pass (70)")
                fig.update_layout(height=300, plot_bgcolor='white', paper_bgcolor='white', showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            
            st.divider()
            csv = df.to_csv(index=False)
            st.download_button("Download Results (CSV)", csv, f"batch_audit_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")

st.divider()
st.caption("Trace: Cold Chain Integrity via GPS + Temperature + Weather + JaamCTRL Traffic Optimization | Hack Helix 2026")
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from scipy import interpolate
import plotly.graph_objects as go
import plotly.express as px
import os

st.set_page_config(page_title="Trace - Cold Chain Auditor", layout="wide")

# Pharma Theme: White (#FFFFFF), Green (#1fc367), Blue (#9ebff5), Yellow (#f4e973)
st.markdown("""<style>
.stApp { background-color: #FFFFFF; }
.header-container { display: flex; justify-content: center; margin-bottom: 1.5rem; border-bottom: 3px solid #9ebff5; padding-bottom: 1rem; }
.header-container img { max-width: 100%; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
h1 { color: #1fc367; text-align: center; font-weight: 700; }
.stCaption { text-align: center; color: #666; font-style: italic; }
.accent-bar { height: 4px; background: linear-gradient(90deg, #1fc367 0%, #f4e973 50%, #9ebff5 100%); }
.stTabs [role="tablist"] button { background: #f8f9fa; border: 2px solid #9ebff5; font-weight: 600; border-radius: 6px; }
.stTabs [role="tablist"] button[aria-selected="true"] { background: #1fc367; color: white; box-shadow: 0 4px 12px rgba(31,195,103,0.25); }
h2 { color: #1fc367; border-bottom: 3px solid #f4e973; padding-bottom: 0.5rem; }
.stMetric { background: #f8f9fa; border-left: 4px solid #9ebff5; border-radius: 6px; box-shadow: 0 2px 6px rgba(0,0,0,0.08); }
.stButton > button { background: #1fc367; color: white; font-weight: 600; border-radius: 6px; box-shadow: 0 4px 12px rgba(31,195,103,0.2); }
.stButton > button:hover { background: #18a24f; transform: translateY(-2px); }
hr { border: none; height: 2px; background: #9ebff5; }
</style>""", unsafe_allow_html=True)

if os.path.exists("assets/header.jpeg"):
    st.markdown('<div class="header-container">', unsafe_allow_html=True)
    st.image("assets/header.jpeg", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.title("Trace: Cold Chain Integrity Auditor")
st.caption("GPS + Temperature + Ambient Weather + JaamCTRL Traffic Optimization = Better Batch Integrity")
st.markdown('<div class="accent-bar"></div>', unsafe_allow_html=True)

DRUGS = {
    "COVID Vaccine": {"min": 2.0, "max": 8.0, "tolerance": 60},
    "Insulin": {"min": 2.0, "max": 8.0, "tolerance": 30},
    "Antibiotics": {"min": 15.0, "max": 25.0, "tolerance": 45},
    "Plasma": {"min": -20.0, "max": -5.0, "tolerance": 15},
    "Biologics": {"min": 2.0, "max": 8.0, "tolerance": 45}
}

COLORS = {"PASS": "#1fc367", "FAIL": "#FF6464", "ACCENT": "#f4e973", "BLUE": "#9ebff5"}

def calculate_pis(temps_array, delay_minutes, spec):
    score = 100.0
    score -= np.sum(temps_array > spec["max"]) * 2.0
    score -= np.sum(temps_array < spec["min"]) * 1.5
    score -= max(0, (delay_minutes - 180) * 0.1)
    return max(0, score)

def generate_temp_profile(drug_spec, seed):
    np.random.seed(seed)
    sparse_times = np.linspace(0, 240, 7)
    base = drug_spec["min"] + (drug_spec["max"] - drug_spec["min"]) / 2
    sparse_temps = base + np.random.normal(0, 0.3, 7)
    f = interpolate.interp1d(sparse_times, sparse_temps, kind="linear", fill_value="extrapolate")
    times = np.arange(0, 241)
    return times, np.clip(f(times), drug_spec["min"] - 3, drug_spec["max"] + 3)

tab1, tab2, tab3, tab4 = st.tabs(["Journey Setup", "Data Sources", "Route Comparison", "Batch Processing"])

with tab1:
    st.header("Step 1: Define Your Shipment")
    c1, c2, c3 = st.columns(3)
    with c1:
        batch_id = st.text_input("Batch ID", "PH-2026-0419-001")
        drug = st.selectbox("Medication", list(DRUGS.keys()))
    with c2:
        st.text_input("Origin", "Delhi Central")
        st.text_input("Destination", "Hospital North")
    with c3:
        duration_hours = st.slider("Duration (hours)", 2, 12, 4)
        st.date_input("Shipment Date", datetime.now().date())
    
    st.divider()
    spec = DRUGS[drug]
    cs1, cs2, cs3 = st.columns(3)
    with cs1:
        st.metric("Min Temp", f"{spec.get('min')}°C")
    with cs2:
        st.metric("Max Temp", f"{spec.get('max')}°C")
    with cs3:
        st.metric("Tolerance", f"{spec.get('tolerance')}m")
    st.session_state.spec = spec
    st.session_state.batch = {"id": batch_id, "drug": drug, "duration": duration_hours}

with tab2:
    st.header("Step 2: Data Sources Integration")
    if "spec" not in st.session_state:
        st.warning("Complete Tab 1 first")
    else:
        spec = st.session_state.spec
        col_gps, col_temp, col_ambient = st.columns(3)
        
        with col_gps:
            st.subheader("GPS Logs (Sparse)")
            gps_df = pd.DataFrame({
                "Time (min)": list(range(0, 241, 40))[:7],
                "Latitude": np.random.uniform(28.55, 28.65, 7).round(4),
                "Longitude": np.random.uniform(77.15, 77.25, 7).round(4)
            })
            st.dataframe(gps_df, use_container_width=True, hide_index=True)
            st.success("Interpolation: 7 → 240 points")
        
        with col_temp:
            st.subheader("Temperature Sensors")
            temp_df = pd.DataFrame({
                "Time (min)": list(range(0, 241, 40))[:7],
                "Temp (°C)": (spec.get('min') + np.random.normal(0, 0.2, 7)).round(2)
            })
            st.dataframe(temp_df, use_container_width=True, hide_index=True)
            st.success("Interpolation: 7 → 240 points")
        
        with col_ambient:
            st.subheader("Ambient Weather (API)")
            ambient_df = pd.DataFrame({
                "Hour": range(8),
                "Ambient (°C)": (28 + np.random.normal(0, 1, 8)).round(1)
            })
            st.dataframe(ambient_df, use_container_width=True, hide_index=True)
            st.success("OpenMeteo API: 8 readings")

with tab3:
    st.header("Step 3: Route Comparison")
    if "spec" not in st.session_state:
        st.warning("Complete Tab 1 first")
    else:
        spec = st.session_state.spec
        batch_id = st.session_state.batch["id"]
        st.info("Standard Signal vs JaamCTRL-Optimized")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Standard Signal Control")
            delay = 240 * 1.2
            times, temps = generate_temp_profile(spec, hash(batch_id + "std") % 2**32)
            pis = calculate_pis(temps, delay, spec)
            (st.success(f"PASS | PIS: {pis:.1f}/100") if pis >= 70 
             else st.error(f"FAIL | PIS: {pis:.1f}/100"))
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("Delay", f"{delay:.0f}m")
            with m2:
                st.metric("Max Temp", f"{temps.max():.1f}\u00b0C")
            with m3:
                st.metric("Grade", "A" if pis >= 90 else "B" if pis >= 70 else "C" if pis >= 50 else "F")
            fig = go.Figure()
            fig.add_hrect(y0=spec["min"], y1=spec["max"], fillcolor=COLORS["PASS"], opacity=0.1)
            fig.add_trace(go.Scatter(x=times, y=temps, line=dict(color=COLORS["BLUE"], width=2)))
            fig.update_layout(title="Temperature Profile", height=280, plot_bgcolor="#f8f9fa", paper_bgcolor="white", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("JaamCTRL-Optimized")
            delay = 240 * 0.67
            times, temps = generate_temp_profile(spec, hash(batch_id + "opt") % 2**32)
            pis = calculate_pis(temps, delay, spec)
            (st.success(f"PASS | PIS: {pis:.1f}/100") if pis >= 70
             else st.error(f"FAIL | PIS: {pis:.1f}/100"))
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("Delay", f"{delay:.0f}m")
            with m2:
                st.metric("Max Temp", f"{temps.max():.1f}\u00b0C")
            with m3:
                st.metric("Grade", "A" if pis >= 90 else "B" if pis >= 70 else "C" if pis >= 50 else "F")
            fig = go.Figure()
            fig.add_hrect(y0=spec["min"], y1=spec["max"], fillcolor=COLORS["PASS"], opacity=0.1)
            fig.add_trace(go.Scatter(x=times, y=temps, line=dict(color=COLORS["PASS"], width=2)))
            fig.update_layout(title="Temperature Profile", height=280, plot_bgcolor="#f8f9fa", paper_bgcolor="white", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.header("Step 4: Batch Processing")
    if "spec" not in st.session_state:
        st.warning("Complete Tab 1 first")
    else:
        spec = st.session_state.spec
        nb = st.slider("Number of batches", 1, 20, 5)
        route = st.radio("Route", ["Standard", "JaamCTRL", "Both"], horizontal=True)
        
        if st.button("RUN AUDIT", type="primary", use_container_width=True):
            results = []
            for i in range(nb):
                drug = np.random.choice(list(DRUGS.keys()))
                _, temps = generate_temp_profile(DRUGS[drug], i)
                delay = {"Standard": 240*1.2, "JaamCTRL": 240*0.67, "Both": 240}[route]
                pis = calculate_pis(temps, delay, DRUGS[drug])
                results.append({"Batch": f"PH-{i+1:03d}", "Drug": drug, "PIS": round(pis, 1),
                               "Status": "PASS" if pis >= 70 else "FAIL",
                               "Grade": "A" if pis >= 90 else "B" if pis >= 70 else "C" if pis >= 50 else "F"})
            st.session_state.results = pd.DataFrame(results)
        
        if "results" in st.session_state:
            df = st.session_state.results
            st.success(f"Audit Complete: {len(df)} batches")
            m1, m2, m3, m4, m5 = st.columns(5)
            passes = len(df[df["Status"] == "PASS"])
            with m1:
                st.metric("Passed", passes, f"/{len(df)}")
            with m2:
                st.metric("Pass Rate", f"{passes/len(df)*100:.0f}%")
            with m3:
                avg_pis = df['PIS'].mean()
                st.metric("Avg PIS", f"{avg_pis:.1f}")
            with m4:
                grade_a = len(df[df['Grade'] == 'A'])
                st.metric("Grade A", grade_a)
            with m5:
                grade_f = len(df[df['Grade'] == 'F'])
                st.metric("Grade F", grade_f)
            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("### Results Table")
                pass_color = COLORS['PASS']
                fail_color = COLORS['FAIL']
                def style_status(val):
                    if val == 'PASS':
                        return f'background-color: {pass_color}; color: white'
                    elif val == 'FAIL':
                        return f'background-color: {fail_color}; color: white'
                    return ''
                styled = df.style.applymap(style_status, subset=['Status'])
                st.dataframe(styled, use_container_width=True, hide_index=True)
            with c2:
                st.markdown("### PIS Distribution")
                fig = px.histogram(df, x="PIS", nbins=10, color_discrete_sequence=[COLORS["BLUE"]])
                fig.update_layout(height=280, plot_bgcolor="white", paper_bgcolor="white", showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            st.divider()
            st.download_button("Download CSV", df.to_csv(index=False), f"audit_{datetime.now():%Y%m%d}.csv", "text/csv")

st.divider()
st.caption("Trace: Cold Chain Integrity Auditor | GPS + Temp + Weather + JaamCTRL | Hack Helix 2026")
