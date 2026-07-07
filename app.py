import json
import time
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from kafka import KafkaConsumer

# --- MASTER'S LEVEL VISUAL CONFIGURATION ---
st.set_page_config(
    page_title="Scalable Cloud Programming CA",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark-mode telemetry layout
st.markdown("""
    <style>
    .metric-container { background-color: #1e2430; padding: 15px; border-radius: 8px; border-left: 5px solid #00f2fe; }
    .status-active { color: #00ff87; font-weight: bold; }
    .status-offline { color: #f43f5e; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR: SYSTEM TELEMETRY CONTROL PANEL ---
st.sidebar.title("🛠️ System Telemetry & Controls")
st.sidebar.markdown("### Lambda Architecture Pipeline Node")
st.sidebar.markdown("**Made By:** Ishan & Vedant")
st.sidebar.markdown("**Stream Infrastructure:** `Apache Kafka`")
st.sidebar.markdown("**Topic ID:** `austin_911_stream`")

# Simulation speed throttling control for evaluation pacing
simulation_pace = st.sidebar.slider("UI Re-evaluation Interval (s)", 0.5, 3.0, 1.0, step=0.5)
clear_buffer = st.sidebar.button("Purge Localized Speed View Cache")

if clear_buffer:
    # Safely clear out the speed serving view file
    if os.path.exists("speed_serving_view.json"):
        try:
            with open("speed_serving_view.json", "w") as f:
                json.dump({}, f)
        except Exception:
            pass
    if 'telemetry_log' in st.session_state:
        st.session_state.telemetry_log = []
    st.toast("Speed Layer localized file cache purged successfully.", icon="🧹")

# --- ARCHITECTURAL DATA INGESTION ENGINE ---
@st.cache_data(ttl=5)
def load_historical_batch_matrix():
    try:
        with open("batch_serving_view.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def load_realtime_speed_matrix():
    """Safely loads real-time counts from disk with thread-safe file handling fallbacks."""
    try:
        if os.path.exists("speed_serving_view.json") and os.path.getsize("speed_serving_view.json") > 0:
            with open("speed_serving_view.json", "r") as f:
                return json.load(f)
        return {}
    except (FileNotFoundError, json.JSONDecodeError):
        # Gracefully handle concurrent write read-locks by falling back to empty state
        return {}

# --- KAFKA INFRASTRUCTURE HEALTH PROBE ---
def evaluate_kafka_cluster_health():
    """Validates connectivity to the local Kafka broker node."""
    try:
        consumer = KafkaConsumer(
            bootstrap_servers=['localhost:9092'],
            request_timeout_ms=1000,
            consumer_timeout_ms=1000
        )
        available_topics = consumer.topics()
        consumer.close()
        
        if "austin_911_stream" in available_topics:
            return "ONLINE (ACTIVE)", "Broker: 9092 | Topic Verified"
        else:
            return "ONLINE (NO TOPIC)", "Broker Alive | Topic Pending"
    except Exception:
        return "OFFLINE", "Local Broker Node Disconnected"

# Read the serving views
batch_data = load_historical_batch_matrix()
speed_data = load_realtime_speed_matrix()

# Execute infrastructure probe
pipeline_status, pipeline_detail = evaluate_kafka_cluster_health()

# Track metadata metrics loop
if 'telemetry_log' not in st.session_state:
    st.session_state.telemetry_log = []

current_live_count = sum(speed_data.values()) if speed_data else 0

# Capture dashboard consumption delta ticks for the layout graph
if pipeline_status.startswith("ONLINE"):
    st.session_state.telemetry_log.append({
        "Timestamp": datetime.now().strftime("%H:%M:%S"),
        "Ingest Count": current_live_count
    })
    if len(st.session_state.telemetry_log) > 15:
        st.session_state.telemetry_log.pop(0)

# --- DASHBOARD MAIN COCKPIT VIEW ---
st.title("🚨 Austin 911 Scalable Lambda Stream Dashboard")
st.caption("Scalable Cloud Programming CA Project")

# 1. Advanced Telemetry Dashboard KPI Header Bar
kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
with kpi_col1:
    status_class = "status-active" if pipeline_status.startswith("ONLINE") else "status-offline"
    st.markdown(f"<div class='metric-container'><b>Pipeline Node Status</b><br><span class='{status_class}'>● {pipeline_status}</span><br><small>{pipeline_detail}</small></div>", unsafe_allow_html=True)
with kpi_col2:
    st.markdown(f"<div class='metric-container'><b>Batch Layer Base</b><br><span style='color:#00f2fe; font-size:24px; font-weight:bold;'>{sum(batch_data.values()):,}</span><br><small>Historical Records Evaluated</small></div>", unsafe_allow_html=True)
with kpi_col3:
    st.markdown(f"<div class='metric-container'><b>Speed Layer Buffer</b><br><span style='color:#fcd34d; font-size:24px; font-weight:bold;'>{current_live_count:,}</span><br><small>Real-Time Delta State</small></div>", unsafe_allow_html=True)
with kpi_col4:
    total_consolidated = sum(batch_data.values()) + current_live_count
    st.markdown(f"<div class='metric-container'><b>Lambda Synthesized Total</b><br><span style='color:#00ff87; font-size:24px; font-weight:bold;'>{total_consolidated:,}</span><br><small>Unified View Records</small></div>", unsafe_allow_html=True)

st.markdown("###")

# 2. Synthesis Matrix (The Lambda Merge Computation Graph)
merged_rows = []
all_incident_categories = set(batch_data.keys()).union(set(speed_data.keys()))

for category in all_incident_categories:
    h_val = batch_data.get(category, 0)
    s_val = speed_data.get(category, 0)
    merged_rows.append({
        "Incident Classification Category": category,
        "Batch Layer (Data Lake Historical Base)": h_val,
        "Speed Layer (Kafka Stream Real-Time Delta)": s_val,
        "Lambda Consolidated Unified View": h_val + s_val
    })

if merged_rows:
    df_core = pd.DataFrame(merged_rows).sort_values(by="Lambda Consolidated Unified View", ascending=False)
else:
    df_core = pd.DataFrame(columns=[
        "Incident Classification Category", 
        "Batch Layer (Data Lake Historical Base)", 
        "Speed Layer (Kafka Stream Real-Time Delta)", 
        "Lambda Consolidated Unified View"
    ])

# 3. Main Analytical Graphical Split Panels
vis_col1, vis_col2 = st.columns([5, 4])

with vis_col1:
    st.markdown("#### 📊 Stacked Lambda Metric Fusion Engine")
    if not df_core.empty:
        top_n_df = df_core.head(8)
        
        fig_stack = go.Figure()
        fig_stack.add_trace(go.Bar(
            name='Batch Historical View',
            x=top_n_df["Incident Classification Category"], 
            y=top_n_df["Batch Layer (Data Lake Historical Base)"],
            marker_color='#1d4ed8'
        ))
        fig_stack.add_trace(go.Bar(
            name='Speed Stream Delta',
            x=top_n_df["Incident Classification Category"], 
            y=top_n_df["Speed Layer (Kafka Stream Real-Time Delta)"],
            marker_color='#f59e0b'
        ))
        
        fig_stack.update_layout(
            barmode='group',  # 🌟 Changed from 'stack' to 'group' to separate the columns side-by-side
            template='plotly_dark',
            height=400,
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        # Apply logarithmic scale to bring out low real-time values alongside high batch figures
        fig_stack.update_yaxes(type="log", title_text="Record Count (Log Scale)")
        
        st.plotly_chart(fig_stack, use_container_width=True)
    else:
        st.info("Awaiting upstream records to generate fusion graph views...")

with vis_col2:
    st.markdown("#### 📈 Speed Layer Accumulation Timeline")
    if st.session_state.telemetry_log:
        df_telemetry = pd.DataFrame(st.session_state.telemetry_log)
        fig_telemetry = px.line(
            df_telemetry, 
            x="Timestamp", 
            y="Ingest Count",
            title="Total Real-Time Records Monitored in Window",
            template="plotly_dark",
            markers=True,
            color_discrete_sequence=["#fcd34d"]
        )
        fig_telemetry.update_layout(height=400, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_telemetry, use_container_width=True)
    else:
        st.info("Awaiting structural stream timeline logs...")

# 4. Enterprise Consolidated Real-time Analytical Ledger Block
st.markdown("---")
st.markdown("#### 🗄️ Unified Lambda Analytics Ledger Schema View")
st.dataframe(
    df_core,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Incident Classification Category": st.column_config.TextColumn("Emergency Incident Classification"),
        "Batch Layer (Data Lake Historical Base)": st.column_config.NumberColumn("Historical Master Archive (Batch)", format="%d"),
        "Speed Layer (Kafka Stream Real-Time Delta)": st.column_config.NumberColumn("Real-Time Sliding State (Speed)", format="%d"),
        "Lambda Consolidated Unified View": st.column_config.NumberColumn("Synthesized Complete Consolidated Output", format="%d")
    }
)

# Automated refresh cycle block
time.sleep(simulation_pace)
st.rerun()