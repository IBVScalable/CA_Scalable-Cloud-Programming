import json
import time
import boto3
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- MASTER'S LEVEL VISUAL CONFIGURATION ---
st.set_page_config(
    page_title="MSc Cloud Computing - Enterprise Lambda Cockpit",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark-mode telemetry layout
st.markdown("""
    <style>
    .metric-container { background-color: #1e2430; padding: 15px; border-radius: 8px; border-left: 5px solid #00f2fe; }
    .status-active { color: #00ff87; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR: SYSTEM TELEMETRY CONTROL PANEL ---
st.sidebar.title("🛠️ System Telemetry & Controls")
st.sidebar.markdown("### Lambda Architecture Pipeline Node")
st.sidebar.markdown("**Made By:** Ishan & Vedant")
st.sidebar.markdown("**Stream ID:** `austin_911_stream`")

# Simulation speed throttling control for evaluation pacing
simulation_pace = st.sidebar.slider("UI Re-evaluation Interval (s)", 0.5, 3.0, 1.0, step=0.5)
clear_buffer = st.sidebar.button("Purge Live Speed Layer Buffer Cache")

if clear_buffer:
    if 'realtime_events' in st.session_state:
        st.session_state.realtime_events = {}
    if 'telemetry_log' in st.session_state:
        st.session_state.telemetry_log = []
    st.toast("Speed Layer localized memory buffer purged successfully.", icon="🧹")

# --- ARCHITECTURAL DATA INGESTION ENGINE ---
@st.cache_data(ttl=60)
def load_historical_batch_matrix():
    try:
        with open("batch_serving_view.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

batch_data = load_historical_batch_matrix()

@st.cache_resource
def initialize_aws_kinesis_session():
    # Instantiates zero-config AWS SDK binding pulling natively from EC2 IAM Profile Role
    return boto3.client('kinesis', region_name="us-east-1")

kinesis = initialize_aws_kinesis_session()
STREAM_NAME = "austin_911_stream"

# Shard Discovery and Session Iterator State Tracking
if 'shard_iterator' not in st.session_state or st.sidebar.button("Force Shard Re-sync"):
    try:
        stream_meta = kinesis.describe_stream(StreamName=STREAM_NAME)
        target_shard = stream_meta['StreamDescription']['Shards'][0]['ShardId']
        st.session_state.active_shard = target_shard
        
        iterator_res = kinesis.get_shard_iterator(
            StreamName=STREAM_NAME,
            ShardId=target_shard,
            ShardIteratorType='LATEST'
        )
        st.session_state.shard_iterator = iterator_res['ShardIterator']
        st.session_state.pipeline_status = "ONLINE (ACTIVE)"
    except Exception as e:
        st.session_state.shard_iterator = None
        st.session_state.active_shard = "N/A"
        st.session_state.pipeline_status = f"DISCONNECTED: {str(e)[:30]}..."

# Initialize buffer dataframes in persistent session scopes
if 'realtime_events' not in st.session_state:
    st.session_state.realtime_events = {}
if 'telemetry_log' not in st.session_state:
    st.session_state.telemetry_log = []

# --- STREAMING EXECUTION BLOCK ---
current_ingest_rate = 0
latency_ms = 0.0

if st.session_state.shard_iterator:
    try:
        t_start = time.time()
        response = kinesis.get_records(ShardIterator=st.session_state.shard_iterator, Limit=50)
        latency_ms = (time.time() - t_start) * 1000 # Evaluate physical network propagation latency
        
        st.session_state.shard_iterator = response['NextShardIterator']
        records = response['Records']
        current_ingest_rate = len(records)
        
        if records:
            for record in records:
                payload = json.loads(record['Data'])
                incident = payload.get('incident_type', 'OTHER')
                st.session_state.realtime_events[incident] = st.session_state.realtime_events.get(incident, 0) + 1
            
            # Record structural metric log to map performance trends
            st.session_state.telemetry_log.append({
                "Timestamp": datetime.now().strftime("%H:%M:%S"),
                "Ingest Count": current_ingest_rate,
                "Network Latency (ms)": latency_ms
            })
            if len(st.session_state.telemetry_log) > 15:
                st.session_state.telemetry_log.pop(0)
    except Exception:
        pass

# --- DASHBOARD MAIN COCKPIT VIEW ---
st.title("🚨 Enterprise Analytics Cockpit — Austin 911 Scalable Lambda Stream Node")
st.caption("Research Project Framework | Scalable Cloud Programming Module Evaluation Context")

# 1. Advanced Telemetry Dashboard KPI Header Bar
kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
with kpi_col1:
    st.markdown(f"<div class='metric-container'><b>Pipeline Node Status</b><br><span class='status-active'>● {st.session_state.pipeline_status}</span><br><small>Shard: {st.session_state.active_shard}</small></div>", unsafe_allow_html=True)
with kpi_col2:
    st.markdown(f"<div class='metric-container'><b>Batch Layer Base</b><br><span style='color:#00f2fe; font-size:24px; font-weight:bold;'>{sum(batch_data.values()):,}</span><br><small>Historical Records Evaluated</small></div>", unsafe_allow_html=True)
with kpi_col3:
    live_total = sum(st.session_state.realtime_events.values())
    st.markdown(f"<div class='metric-container'><b>Speed Layer Buffer</b><br><span style='color:#fcd34d; font-size:24px; font-weight:bold;'>{live_total:,}</span><br><small>Delta Events Ingested</small></div>", unsafe_allow_html=True)
with kpi_col4:
    avg_latency = pd.DataFrame(st.session_state.telemetry_log)["Network Latency (ms)"].mean() if st.session_state.telemetry_log else latency_ms
    st.markdown(f"<div class='metric-container'><b>SDK Fetch Latency</b><br><span style='color:#f43f5e; font-size:24px; font-weight:bold;'>{avg_latency:.2f} ms</span><br><small>Kinesis GetRecords Frame Duration</small></div>", unsafe_allow_html=True)

st.markdown("###")

# 2. Synthesis Matrix (The Lambda Merge Computation Graph)
merged_rows = []
all_incident_categories = set(batch_data.keys()).union(set(st.session_state.realtime_events.keys()))

for category in all_incident_categories:
    h_val = batch_data.get(category, 0)
    s_val = st.session_state.realtime_events.get(category, 0)
    merged_rows.append({
        "Incident Classification Category": category,
        "Batch Layer (Data Lake Historical Base)": h_val,
        "Speed Layer (Kinesis Stream Real-Time Delta)": s_val,
        "Lambda Consolidated Unified View": h_val + s_val
    })

df_core = pd.DataFrame(merged_rows).sort_values(by="Lambda Consolidated Unified View", ascending=False)

# 3. Main Analytical Graphical Split Panels
vis_col1, vis_col2 = st.columns([5, 4])

with vis_col1:
    st.markdown("#### 📊 Stacked Lambda Metric Fusion Engine")
    # Show the topmost common distribution profiles
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
        y=top_n_df["Speed Layer (Kinesis Stream Real-Time Delta)"],
        marker_color='#f59e0b'
    ))
    
    fig_stack.update_layout(
        barmode='stack',
        template='plotly_dark',
        height=400,
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_stack, use_container_width=True)

with vis_col2:
    st.markdown("#### 📈 Network & Consumer Throughput Stream Timeline")
    if st.session_state.telemetry_log:
        df_telemetry = pd.DataFrame(st.session_state.telemetry_log)
        fig_telemetry = px.line(
            df_telemetry, 
            x="Timestamp", 
            y="Ingest Count",
            title="Stream Ingestion Records per Cycle Boundary",
            template="plotly_dark",
            markers=True,
            color_discrete_sequence=["#00ff87"]
        )
        fig_telemetry.update_layout(height=400, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_telemetry, use_container_width=True)
    else:
        st.info("Awaiting structural stream payload cycles to map timeline visualization patterns...")

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
        "Speed Layer (Kinesis Stream Real-Time Delta)": st.column_config.NumberColumn("Real-Time Sliding State (Speed)", format="%d"),
        "Lambda Consolidated Unified View": st.column_config.NumberColumn("Synthesized Complete Consolidated Output", format="%d")
    }
)

# Automated refresh cycle block
time.sleep(simulation_pace)
st.rerun()