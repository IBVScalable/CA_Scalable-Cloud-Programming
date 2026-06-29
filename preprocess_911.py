import os
import io
import pandas as pd
import numpy as np
import boto3

# =====================================================================
# 1. INITIALIZATION & CREDENTIAL FETCH
# =====================================================================
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")

if not all([AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_SESSION_TOKEN]):
    raise ValueError("Missing active AWS environment variables for processing.")

session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    aws_session_token=AWS_SESSION_TOKEN,
    region_name="us-east-1"
)
s3 = session.client('s3')

# Match your exact bucket configuration
BUCKET_NAME = "nci-911-austin-project-2026"  
INPUT_FILE_KEY = "austin_911_raw_api_data.csv"
OUTPUT_FILE_KEY = "austin_911_cleaned_features.csv"

print(f"Pulling raw file from cloud storage: s3://{BUCKET_NAME}/{INPUT_FILE_KEY}")
obj = s3.get_object(Bucket=BUCKET_NAME, Key=INPUT_FILE_KEY)
df = pd.read_csv(io.BytesIO(obj['Body'].read()))
print(f"Matrix loaded. Starting operations on {df.shape[0]} rows...")

# =====================================================================
# 2. TARGET VARIANT EXTRACTION (OPTION B)
# =====================================================================
# Strip rows missing the priority classification
df = df.dropna(subset=['priority_level'])

# Clean text formatting artifacts out of the label to preserve raw integers
df['priority_level'] = df['priority_level'].astype(str).str.extract(r'(\d+)').astype(int)

# =====================================================================
# 3. DYNAMIC COLUMN DETECTION & TEMPORAL FEATURE ENGINEERING
# =====================================================================
print("Raw columns found in dataset:", list(df.columns))

# Find the best column match for time data
time_col = None
possible_time_cols = ['call_arrival_time_hour_and_minute', 'call_time', 'interchange_call_time', 'incident_date']

for col in possible_time_cols:
    if col in df.columns:
        time_col = col
        break

if not time_col:
    # Fallback search for any column with 'time' or 'date' in the name
    for col in df.columns:
        if 'time' in col.lower() or 'date' in col.lower():
            time_col = col
            break

if time_col:
    print(f"Engineering cyclical date-time attributes using column: '{time_col}'")
    df['call_time'] = pd.to_datetime(df[time_col], errors='coerce')
    
    # Handle cases where parsing might return NaT (Not a Time)
    df = df.dropna(subset=['call_time'])
    
    df['hour_of_day'] = df['call_time'].dt.hour
    df['day_of_week'] = df['call_time'].dt.dayofweek
    df['month'] = df['call_time'].dt.month
    df['is_weekend'] = df['day_of_week'].apply(lambda x: 1 if x >= 5 else 0)
else:
    print("WARNING: No explicit datetime column located. Injecting default benchmark fields.")
    df['hour_of_day'] = 12
    df['day_of_week'] = 2
    df['month'] = 6
    df['is_weekend'] = 0

# =====================================================================
# 4. CATEGORICAL DIMENSION REDUCTION WITH SAFE GUARDRAILS
# =====================================================================
print("Processing spatial and dispatch categorical keys...")

# Safe fallback checks for categorical layers
sector_col = 'sector' if 'sector' in df.columns else (df.columns[4] if len(df.columns) > 4 else df.columns[0])
type_col = 'dispatched_incident_type' if 'dispatched_incident_type' in df.columns else (df.columns[2] if len(df.columns) > 2 else df.columns[0])

df['sector'] = df[sector_col].fillna('UNKNOWN').astype(str)
df['dispatched_incident_type'] = df[type_col].fillna('UNKNOWN').astype(str)

# Group sparse, high-cardinality variants
incident_counts = df['dispatched_incident_type'].value_counts()
major_incidents = incident_counts.index[incident_counts >= 150]
df['incident_type_cleaned'] = df['dispatched_incident_type'].apply(lambda x: x if x in major_incidents else 'OTHER')

# Process Mental Health Flags if available
df['is_mental_health'] = 0
for col in df.columns:
    if 'mental' in col.lower():
        df['is_mental_health'] = df[col].fillna('').apply(lambda x: 1 if 'mental' in str(x).lower() or '1' in str(x) else 0)
        break
# =====================================================================
# 5. SYNCHRONIZE ANALYTICAL MATRIX BACK TO S3
# =====================================================================
# Isolate only the engineered feature engineering pillars
clean_features = [
    'hour_of_day', 'day_of_week', 'month', 'is_weekend',
    'sector', 'incident_type_cleaned', 'is_mental_health', 'priority_level'
]
df_clean = df[clean_features].copy()

print(f"Uploading polished modeling array shape: {df_clean.shape}")
csv_buffer = io.StringIO()
df_clean.to_csv(csv_buffer, index=False)
s3.put_object(Bucket=BUCKET_NAME, Key=OUTPUT_FILE_KEY, Body=csv_buffer.getvalue())

print(f"SUCCESS: Preprocessed dataset stored as: s3://{BUCKET_NAME}/{OUTPUT_FILE_KEY}")
