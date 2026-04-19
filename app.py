"""
Trace - Cold Chain Batch Integrity Auditor v3.0
Complete 4-tab workflow: Journey Setup > Data Sources > Data Integration > Batch Processing
GPS + Temperature Sensors + Ambient API + PIS Calculation
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json
import plotly.graph_objects as go
import plotly.express as px
from scipy import interpolate
import requests

WHITE = "#FFFFFF"
GREEN = "#1fc367"
BLUE = "#9ebff5"
YELLOW = "#f4e973"
BLACK = "#000000"
RED = "#FF6464"
GREY = "#a6b2b0"

st.set_page_config(page_title="Trace - Cold Chain Auditor", page_icon="", layout="wide")

custom_css = f"""
<style>
    .stApp {{ background-color: {WHITE}; }}
    .stButton > button {{
        background-color: {GREEN} !important;
        color: {WHITE} !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 10px 20px !important;
        box-shadow: 0 2px 8px rgba(31, 195, 103, 0.2);
    }}
    .stButton > button:hover {{ background-color: #16a153 !important; }}
    .stMetric {{
        background-color: {WHITE};
        border: 2px solid {GREEN};
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 2px 6px rgba(158, 191, 245, 0.15);
    }}
    .stMetric label {{ color: {GREY} !important; font-weight: 600; }}
    .stMetric-value {{ color: {GREEN} !important; font-size: 28px !important; font-weight: bold; }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 8px; background-color: transparent; }}
    .stTabs [data-baseweb="tab"] {{
        padding: 12px 20px !important;
        border-radius: 8px 8px 0 0 !important;
        background-color: {WHITE};
        border: 2px solid {BLUE};
        border-bottom: none;
        color: {GREY} !important;
        font-weight: 600;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {GREEN} !important;
        border: 2px solid {GREEN} !important;
        color: {WHITE} !important;
    }}
    hr {{ border: none; height: 2px; background: linear-gradient(to right, {GREEN}, {BLUE}, {YELLOW}); margin: 20px 0; }}
    .stTextInput input, .stSelectbox select {{ background-color: {WHITE} !important; color: {BLACK} !important; border: 2px solid {BLUE} !important; border-radius: 8px !important; }}
    .stAlert.success {{ background-color: rgba(31, 195, 103, 0.1) !important; border-left: 5px solid {GREEN} !important; color: {GREEN} !important; }}
    .stAlert.warning {{ background-color: rgba(244, 233, 115, 0.15) !important; border-left: 5px solid {YELLOW} !important; }}
    .stAlert.error {{ background-color: rgba(255, 100, 100, 0.1) !important; border-left: 5px solid {RED} !important; }}
    .stAlert.info {{ background-color: rgba(158, 191, 245, 0.15) !important; border-left: 5px solid {BLUE} !important; }}
    h1 {{ color: {GREEN} !important; font-weight: 700; }}
    h2 {{ color: {GREEN} !important; font-weight: 700; border-bottom: 3px solid {BLUE}; padding-bottom: 10px; }}
    h3 {{ color: {BLACK} !important; font-weight: 600; }}
    .pass-badge {{ background-color: {GREEN}; color: {WHITE}; padding: 20px; border-radius: 10px; text-align: center; font-weight: bold; font-size: 32px; }}
    .fail-badge {{ background-color: {RED}; color: {WHITE}; padding: 20px; border-radius: 10px; text-align: center; font-weight: bold; font-size: 32px; }}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

header_path = os.path.join(os.path.dirname(__file__), "assets", "header.jpeg")
if os.path.exists(header_path):
    st.image(header_path, use_container_width=True)

st.markdown(f"<h1>Trace: Cold Chain Integrity Auditor</h1>", unsafe_allow_html=True)
st.caption("GPS Logs + Temperature Sensors + Ambient API + JaamCTRL Traffic Intelligence | Hack Helix 2026")

st.divider()

drug_specs = {
    "COVID Vaccine": {"min": 2.0, "max": 8.0},
    "Insulin": {"min": 2.0, "max": 8.0},
    "Antibiotics": {"min": 15.0, "max": 25.0},
    "Plasma": {"min": -20.0, "max": -5.0},
    "Biologics": {"min": 2.0, "max": 8.0}
}

tab1, tab2, tab3, tab4 = st.tabs([
    "Journey Setup",
    "Data Sources",
    "Data Integration",
    "Batch Processing"
])

progress_keeper = st.session_state

with tab1:
    st.markdown("## Step 1: Define Shipment Journey")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### Batch Information")
        batch_id = st.text_input("Batch ID", "PH-2026-0419-001")
        drug = st.selectbox("Medication", list(drug_specs.keys()))
    
    with col2:
        st.markdown("### Route Details")
        origin = st.text_input("Origin", "Delhi Central Pharma")
        destination = st.text_input("Destination", "Hospital Chain North")
    
    with col3:
        st.markdown("### Journey Duration")
        duration_hours = st.slider("Expected Journey (hours)", 2, 12, 4)
        start_date = st.date_input("Journey Date", datetime.now().date())
    
    st.divider()
    
    spec = drug_specs[drug]
    
    st.markdown("### Temperature Specifications")
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        st.metric("Min Temp", f"{spec['min']}°C")
    with col_s2:
        st.metric("Max Temp", f"{spec['max']}°C")
    with col_s3:
        st.metric("Range", f"{spec['max'] - spec['min']}°C")
    
    st.divider()
    
    st.markdown("### Route Selection")
    route_choice = st.radio(
        "Transport Route",
        ["Standard Signal", "JaamCTRL-Optimized", "Both"],
        horizontal=True
    )
    
    if route_choice == "Standard Signal":
        delay_minutes = duration_hours * 60 * 1.2
        traffic_density = 0.70
    elif route_choice == "JaamCTRL-Optimized":
        delay_minutes = duration_hours * 60 * 0.67
        traffic_density = 0.15
    else:
        delay_minutes = duration_hours * 60
        traffic_density = 0.42
    
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        st.success(f"Estimated Delay: {delay_minutes:.0f} minutes")
    with col_r2:
        st.info(f"Traffic Density: {traffic_density*100:.0f}%")
    
    st.session_state.journey_config = {
        'batch_id': batch_id,
        'drug': drug,
        'origin': origin,
        'destination': destination,
        'duration_hours': duration_hours,
        'start_date': start_date,
        'route_choice': route_choice,
        'delay_minutes': delay_minutes,
        'traffic_density': traffic_density,
        'spec': spec
    }

with tab2:
    st.markdown("## Step 2: Data Sources")
    
    if 'journey_config' not in st.session_state:
        st.warning("Please complete Tab 1: Journey Setup first")
    else:
        config = st.session_state.journey_config
        journey_minutes = int(config['duration_hours'] * 60)
        spec = config['spec']
        
        with st.expander("GPS Coordinates (Sparse)", expanded=True):
            st.markdown("""
            Vehicle GPS tracker records position every 15-30 minutes (sparse data).
            Interpolated to 1-minute granularity using cubic spline.
            """)
            
            sparse_gps_times = np.linspace(0, journey_minutes, 7)
            sparse_lats = 28.6 + np.sin(sparse_gps_times / 40) * 0.05 + np.random.normal(0, 0.01, len(sparse_gps_times))
            sparse_lons = 77.2 + np.cos(sparse_gps_times / 40) * 0.05 + np.random.normal(0, 0.01, len(sparse_gps_times))
            
            gps_df = pd.DataFrame({
                'Time (min)': sparse_gps_times.astype(int),
                'Latitude': sparse_lats.round(4),
                'Longitude': sparse_lons.round(4)
            })
            
            st.markdown("#### Sparse GPS Readings")
            st.dataframe(gps_df, use_container_width=True, hide_index=True)
            st.caption(f"Total readings: {len(gps_df)} | Journey: {journey_minutes} min | Intervals: ~{int(journey_minutes/len(gps_df))} min")
            
            f_lat = interpolate.CubicSpline(sparse_gps_times, sparse_lats)
            f_lon = interpolate.CubicSpline(sparse_gps_times, sparse_lons)
            dense_gps_times = np.arange(0, journey_minutes + 1)
            dense_lats = f_lat(dense_gps_times)
            dense_lons = f_lon(dense_gps_times)
            
            st.success(f"Cubic Spline Interpolation: {len(gps_df)} points -> {len(dense_gps_times)} points")
            
            fig_gps = go.Figure()
            fig_gps.add_trace(go.Scatter(x=sparse_lons, y=sparse_lats, mode='markers',
                name='Sparse GPS', marker=dict(size=10, color=RED, symbol='diamond')))
            fig_gps.add_trace(go.Scatter(x=dense_lons, y=dense_lats, mode='lines',
                name='Interpolated Route', line=dict(color=BLUE, width=2)))
            fig_gps.update_layout(title='Route Reconstruction from Sparse GPS',
                xaxis_title='Longitude', yaxis_title='Latitude', height=400,
                plot_bgcolor=WHITE, paper_bgcolor=WHITE, hovermode='closest')
            st.plotly_chart(fig_gps, use_container_width=True)
            
            st.session_state.gps_data = {
                'sparse_times': sparse_gps_times,
                'dense_times': dense_gps_times,
                'dense_lats': dense_lats,
                'dense_lons': dense_lons
            }
        
        with st.expander("Temperature Sensors (Sparse)", expanded=True):
            st.markdown("""
            Temperature data loggers record readings every 30-45 minutes (sparse).
            Reconstructed to full journey profile using linear interpolation.
            """)
            
            sparse_temp_times = np.array([0, 30, 60, 90, 120, 180, journey_minutes])[:7]
            sparse_temps = spec['min'] + np.random.normal(0, 0.3, len(sparse_temp_times))
            
            temp_df = pd.DataFrame({
                'Time (min)': sparse_temp_times.astype(int),
                'Temperature (°C)': sparse_temps.round(2)
            })
            
            st.markdown("#### Sparse Temperature Readings")
            st.dataframe(temp_df, use_container_width=True, hide_index=True)
            st.caption(f"Total readings: {len(temp_df)} | Coverage: {journey_minutes} min")
            
            f_temp = interpolate.interp1d(sparse_temp_times, sparse_temps, kind='linear', fill_value='extrapolate')
            dense_temp_times = np.arange(0, journey_minutes + 1)
            dense_temps = f_temp(dense_temp_times)
            dense_temps = np.clip(dense_temps, spec['min'] - 5, spec['max'] + 5)
            
            st.success(f"Linear Interpolation: {len(temp_df)} points -> {len(dense_temp_times)} points")
            
            fig_temp = go.Figure()
            fig_temp.add_hline(y=spec['max'], line_dash="dash", line_color=RED, annotation_text=f"Spec Max ({spec['max']}°C)")
            fig_temp.add_hline(y=spec['min'], line_dash="dash", line_color=RED, annotation_text=f"Spec Min ({spec['min']}°C)")
            fig_temp.add_hrect(y0=spec['min'], y1=spec['max'], fillcolor=GREEN, opacity=0.1, layer="below")
            fig_temp.add_trace(go.Scatter(x=sparse_temp_times, y=sparse_temps, mode='markers',
                name='Sensor Readings', marker=dict(size=10, color=YELLOW, symbol='circle')))
            fig_temp.add_trace(go.Scatter(x=dense_temp_times, y=dense_temps, mode='lines',
                name='Reconstructed', line=dict(color=BLUE, width=2)))
            fig_temp.update_layout(title=f'Temperature Profile - {config["drug"]}',
                xaxis_title='Journey Time (minutes)', yaxis_title='Temperature (°C)',
                height=400, plot_bgcolor=WHITE, paper_bgcolor=WHITE, hovermode='x unified')
            st.plotly_chart(fig_temp, use_container_width=True)
            
            st.session_state.temp_data = {
                'sparse_times': sparse_temp_times,
                'sparse_temps': sparse_temps,
                'dense_times': dense_temp_times,
                'dense_temps': dense_temps
            }
        
        with st.expander("Ambient Weather (OpenMeteo API)", expanded=True):
            st.markdown("""
            Real-time weather data from OpenMeteo API (free, no authentication).
            Fetches ambient temperature for Delhi (28.63°N, 77.22°E).
            """)
            
            try:
                lat, lon = 28.6315, 77.2167
                start_str = config['start_date'].isoformat()
                end_str = (config['start_date'] + timedelta(days=1)).isoformat()
                
                url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={start_str}&end_date={end_str}&hourly=temperature_2m"
                
                with st.spinner("Fetching ambient weather..."):
                    response = requests.get(url, timeout=5)
                    weather_data = response.json()
                
                if 'hourly' in weather_data:
                    ambient_temps = weather_data['hourly']['temperature_2m']
                    ambient_times = np.linspace(0, journey_minutes, len(ambient_temps))
                    
                    st.success(f"API Connected | Records: {len(ambient_temps)} | Location: Delhi (28.63N, 77.22E)")
                    
                    col_amb1, col_amb2, col_amb3 = st.columns(3)
                    with col_amb1:
                        st.metric("Min Ambient", f"{min(ambient_temps):.1f}°C")
                    with col_amb2:
                        st.metric("Max Ambient", f"{max(ambient_temps):.1f}°C")
                    with col_amb3:
                        st.metric("Mean Ambient", f"{np.mean(ambient_temps):.1f}°C")
                    
                    fig_amb = px.line(x=ambient_times, y=ambient_temps,
                        title='Ambient Temperature Timeline (OpenMeteo)',
                        labels={'x': 'Time (min)', 'y': 'Temperature (°C)'})
                    fig_amb.update_layout(height=300, plot_bgcolor=WHITE, paper_bgcolor=WHITE)
                    st.plotly_chart(fig_amb, use_container_width=True)
                    
                    st.session_state.ambient_data = {'times': ambient_times, 'temps': ambient_temps}
                    
            except Exception as e:
                st.warning(f"API fetch issue: {str(e)}")
                st.info("Using fallback ambient data (28°C)")
                st.session_state.ambient_data = {'times': np.linspace(0, journey_minutes, 24), 'temps': np.full(24, 28.0)}

with tab3:
    st.markdown("## Step 3: Integrated Data Analysis")
    
    if 'journey_config' not in st.session_state or 'gps_data' not in st.session_state:
        st.warning("Please complete Tabs 1 and 2 first")
    else:
        config = st.session_state.journey_config
        gps = st.session_state.gps_data
        temp = st.session_state.temp_data
        spec = config['spec']
        
        col_map, col_temp_prof, col_metrics = st.columns([1, 1, 1])
        
        with col_map:
            st.markdown("### Route Map")
            fig_route = go.Figure()
            fig_route.add_trace(go.Scatter(x=gps['dense_lons'], y=gps['dense_lats'], mode='lines',
                line=dict(color=BLUE, width=3), name='Route'))
            fig_route.add_trace(go.Scatter(x=[gps['dense_lons'][0]], y=[gps['dense_lats'][0]], mode='markers',
                marker=dict(size=12, color=GREEN, symbol='star'), name='Start'))
            fig_route.add_trace(go.Scatter(x=[gps['dense_lons'][-1]], y=[gps['dense_lats'][-1]], mode='markers',
                marker=dict(size=12, color=RED, symbol='diamond'), name='End'))
            fig_route.update_layout(title='Vehicle Route', height=350, plot_bgcolor=WHITE, paper_bgcolor=WHITE,
                xaxis_title='Longitude', yaxis_title='Latitude')
            st.plotly_chart(fig_route, use_container_width=True)
        
        with col_temp_prof:
            st.markdown("### Temperature Profile")
            fig_t = go.Figure()
            fig_t.add_hrect(y0=spec['min'], y1=spec['max'], fillcolor=GREEN, opacity=0.1, layer="below")
            fig_t.add_hline(y=spec['max'], line_dash="dash", line_color=RED)
            fig_t.add_hline(y=spec['min'], line_dash="dash", line_color=RED)
            fig_t.add_trace(go.Scatter(x=temp['dense_times'], y=temp['dense_temps'], mode='lines',
                line=dict(color=BLUE, width=3), name='Temperature'))
            fig_t.update_layout(title='Cold Chain Profile', height=350, plot_bgcolor=WHITE, paper_bgcolor=WHITE,
                xaxis_title='Time (min)', yaxis_title='Temp (°C)')
            st.plotly_chart(fig_t, use_container_width=True)
        
        with col_metrics:
            st.markdown("### Quality Metrics")
            
            excursions = np.sum((temp['dense_temps'] < spec['min']) | (temp['dense_temps'] > spec['max']))
            time_above = np.sum(temp['dense_temps'] > spec['max']) * (len(temp['dense_temps']) / len(temp['dense_times']))
            time_below = np.sum(temp['dense_temps'] < spec['min']) * (len(temp['dense_temps']) / len(temp['dense_times']))
            
            pis = max(0, 100 - (excursions * 2) - (time_above * 0.15) - (time_below * 0.1) - (config['delay_minutes'] * 0.5))
            status = "PASS" if pis >= 70 else "FAIL"
            
            if status == "PASS":
                st.markdown(f"<div class='pass-badge'>PASS<br>{pis:.0f}/100</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='fail-badge'>FAIL<br>{pis:.0f}/100</div>", unsafe_allow_html=True)
            
            st.markdown(f"""
Excursions: {int(excursions)}
Time Above: {time_above:.0f} min
Time Below: {time_below:.0f} min
Delay: {config['delay_minutes']:.0f} min
            """)
            
            st.session_state.pis_result = {'score': pis, 'status': status, 'excursions': excursions}

with tab4:
    st.markdown("## Step 4: Batch Processing Workflow")
    
    st.markdown("Process multiple batches through the complete pipeline")
    
    num_batches = st.slider("Number of Batches to Process", 1, 20, 5)
    
    st.divider()
    
    if st.button("Run Batch Audit", type="primary", use_container_width=True):
        batch_results = []
        
        with st.spinner(f"Processing {num_batches} batches..."):
            np.random.seed(42)
            
            for i in range(num_batches):
                drug_choice = np.random.choice(list(drug_specs.keys()))
                spec_choice = drug_specs[drug_choice]
                journey_min = np.random.randint(180, 360)
                
                sparse_t = np.linspace(0, journey_min, np.random.randint(5, 8))
                sparse_temp = spec_choice['min'] + np.random.normal(0, 0.5, len(sparse_t))
                f_t = interpolate.interp1d(sparse_t, sparse_temp, kind='linear', fill_value='extrapolate')
                dense_t = np.arange(0, journey_min)
                dense_temp = f_t(dense_t)
                dense_temp = np.clip(dense_temp, spec_choice['min'] - 5, spec_choice['max'] + 5)
                
                excursions = np.sum((dense_temp < spec_choice['min']) | (dense_temp > spec_choice['max']))
                time_above = np.sum(dense_temp > spec_choice['max']) * (journey_min / len(dense_t))
                time_below = np.sum(dense_temp < spec_choice['min']) * (journey_min / len(dense_t))
                delay = np.random.randint(25, 65)
                
                pis = max(0, 100 - (excursions * 2) - (time_above * 0.15) - (time_below * 0.1) - (delay * 0.5))
                status = "PASS" if pis >= 70 else "FAIL"
                
                batch_results.append({
                    "Batch ID": f"PH-2026-0419-{i+1:03d}",
                    "Drug": drug_choice,
                    "Duration (min)": journey_min,
                    "Excursions": int(excursions),
                    "Time Above (min)": f"{time_above:.0f}",
                    "Delay (min)": delay,
                    "PIS Score": round(pis, 1),
                    "Status": status,
                    "Grade": 'A' if pis >= 90 else 'B' if pis >= 70 else 'C' if pis >= 50 else 'F'
                })
        
        st.session_state.batch_results = batch_results
    
    if 'batch_results' in st.session_state:
        results_df = pd.DataFrame(st.session_state.batch_results)
        
        st.success(f"Audit Complete: {len(results_df)} batches processed")
        
        st.markdown("### Summary Metrics")
        
        col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
        with col_m1:
            pass_count = len(results_df[results_df['Status'] == 'PASS'])
            st.metric("Batches Passed", pass_count, f"/{len(results_df)}")
        with col_m2:
            st.metric("Pass Rate", f"{(pass_count/len(results_df))*100:.0f}%")
        with col_m3:
            avg_pis = results_df['PIS Score'].mean()
            st.metric("Avg PIS", f"{avg_pis:.1f}/100")
        with col_m4:
            grade_a = len(results_df[results_df['Grade'] == 'A'])
            st.metric("Grade A", grade_a)
        with col_m5:
            avg_delay = results_df['Delay (min)'].astype(int).mean()
            st.metric("Avg Delay", f"{avg_delay:.0f} min")
        
        st.divider()
        
        st.markdown("### Results Table")
        
        def style_status(val):
            if val == 'PASS':
                return f'background-color: {GREEN}; color: {WHITE}'
            else:
                return f'background-color: {RED}; color: {WHITE}'
        
        styled_df = results_df.style.applymap(lambda x: style_status(x) if x in ['PASS', 'FAIL'] else '', subset=['Status'])
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        st.divider()
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.markdown("### PIS Distribution")
            fig_dist = px.histogram(results_df, x='PIS Score', nbins=12,
                title='PIS Score Distribution', color_discrete_sequence=[BLUE])
            fig_dist.add_vline(x=70, line_dash="dash", line_color=GREEN,
                annotation_text="Pass Threshold (70)")
            fig_dist.update_layout(height=350, plot_bgcolor=WHITE, paper_bgcolor=WHITE)
            st.plotly_chart(fig_dist, use_container_width=True)
        
        with col_chart2:
            st.markdown("### Status Breakdown")
            status_counts = results_df['Status'].value_counts()
            fig_status = px.pie(values=status_counts.values, names=status_counts.index,
                color=status_counts.index, color_discrete_map={'PASS': GREEN, 'FAIL': RED},
                title='Pass/Fail Distribution')
            fig_status.update_layout(height=350, plot_bgcolor=WHITE, paper_bgcolor=WHITE)
            st.plotly_chart(fig_status, use_container_width=True)
        
        st.divider()
        
        st.markdown("### Export Results")
        csv = results_df.to_csv(index=False)
        st.download_button("Download Batch Results (CSV)", csv, "batch_audit.csv", "text/csv")

st.divider()
st.caption("Trace integrates GPS interpolation + temperature reconstruction + ambient weather + traffic optimization insights")
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

custom_css = f"""
<style>
    .stApp {{
        background-color: {WHITE};
        color: {BLACK};
    }}
    
    .stButton > button {{
        background-color: {GREEN} !important;
        color: {WHITE} !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 10px 20px !important;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(31, 195, 103, 0.2);
    }}
    
    .stButton > button:hover {{
        background-color: #16a153 !important;
        box-shadow: 0 4px 12px rgba(31, 195, 103, 0.3);
    }}
    
    .stMetric {{
        background-color: {WHITE};
        border: 2px solid {GREEN};
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 2px 6px rgba(158, 191, 245, 0.15);
    }}
    
    .stMetric label {{
        color: {GREY} !important;
        font-weight: 600;
    }}
    
    .stMetric-value {{
        color: {GREEN} !important;
        font-size: 28px !important;
        font-weight: bold;
    }}
    
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background-color: transparent;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        padding: 12px 20px !important;
        border-radius: 8px 8px 0 0 !important;
        background-color: {WHITE};
        border: 2px solid {BLUE};
        border-bottom: none;
        color: {GREY} !important;
        font-weight: 600;
    }}
    
    .stTabs [aria-selected="true"] {{
        background-color: {GREEN} !important;
        border: 2px solid {GREEN} !important;
        color: {WHITE} !important;
    }}
    
    hr {{
        border: none;
        height: 2px;
        background: linear-gradient(to right, {GREEN}, {BLUE}, {YELLOW});
        margin: 20px 0;
    }}
    
    .stTextInput input, .stSelectbox select, .stNumberInput input {{
        background-color: {WHITE} !important;
        color: {BLACK} !important;
        border: 2px solid {BLUE} !important;
        border-radius: 8px !important;
    }}
    
    .stCheckbox {{
        background-color: transparent;
    }}
    
    .stAlert.success {{
        background-color: rgba(31, 195, 103, 0.1) !important;
        border-left: 5px solid {GREEN} !important;
        color: {GREEN} !important;
    }}
    
    .stAlert.warning {{
        background-color: rgba(244, 233, 115, 0.15) !important;
        border-left: 5px solid {YELLOW} !important;
        color: {BLACK} !important;
    }}
    
    .stAlert.error {{
        background-color: rgba(255, 100, 100, 0.1) !important;
        border-left: 5px solid #FF6464 !important;
        color: {BLACK} !important;
    }}
    
    .stAlert.info {{
        background-color: rgba(158, 191, 245, 0.15) !important;
        border-left: 5px solid {BLUE} !important;
        color: {BLACK} !important;
    }}
    
    h1 {{
        color: {GREEN} !important;
        font-weight: 700;
    }}
    
    h2 {{
        color: {GREEN} !important;
        font-weight: 700;
        border-bottom: 3px solid {BLUE};
        padding-bottom: 10px;
    }}
    
    h3 {{
        color: {BLACK} !important;
        font-weight: 600;
    }}
    
    p {{
        color: {BLACK};
    }}
    
    .stCaption {{
        color: {GREY} !important;
        font-weight: 500;
    }}
    
    .stSidebar {{
        background-color: {WHITE};
        border-right: 2px solid {BLUE};
    }}
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)

header_path = os.path.join(os.path.dirname(__file__), "assets", "header.jpeg")
if os.path.exists(header_path):
    st.image(header_path, use_container_width=True)

col1, col2 = st.columns([3, 1])
with col1:
    st.markdown(f"<p style='color: {GREY}; font-size: 14px; font-weight: 500;'>Pharmaceutical Cold Chain Integrity Auditor | Powered by JaamCTRL Traffic Intelligence</p>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<p style='color: {GREY}; font-size: 12px; text-align: right;'>Hack Helix 2026 | Track 3, Problem 02</p>", unsafe_allow_html=True)

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
