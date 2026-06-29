import os
import io
import requests
import pandas as pd
import boto3
 
# =====================================================================
# 1. ENVIRONMENT SECURITY & AWS ACADEMY INITIALIZATION
# =====================================================================
# Read secure variables set up in your local EC2 environment or GitHub Secrets
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")
 
# Fail early if credentials are missing
if not all([AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_SESSION_TOKEN]):
    raise ValueError(
        "Missing temporary AWS credentials! Ensure AWS_ACCESS_KEY_ID, "
        "AWS_SECRET_ACCESS_KEY, and AWS_SESSION_TOKEN are set in your environment."
    )
 
# Establish a session bound by your AWS Academy temporary LabRole restrictions
session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    aws_session_token=AWS_SESSION_TOKEN,
    region_name="us-east-1"
)
s3 = session.client('s3')
 
# =====================================================================
# 2. CONFIGURATION CHANNELS
# =====================================================================
# The clean data resource endpoint path for the Socrata backend
API_ENDPOINT = "https://data.austintexas.gov/resource/e687-fx2y.json"
 
# Update this to match your EXACT bucket name created in the AWS console
BUCKET_NAME = "nci-911-austin-project-2026"  
MASTER_FILE_KEY = "austin_911_raw_api_data.csv"
 
# Configuration variables for handling scalable cloud sampling benchmarks
LIMIT_PER_PAGE = 5000       # Efficient batch size allowed by Socrata
TOTAL_ROWS_NEEDED = 60000   # Solid size to build performance vs throughput graphs
all_records = []
 
# =====================================================================
# 3. PAGINATED DATA EXTRACTION INGESTION ENGINE
# =====================================================================
print(f"Initializing live stream ingestion from: {API_ENDPOINT}")
print(f"Targeting sample capacity: {TOTAL_ROWS_NEEDED} rows...")
 
for offset in range(0, TOTAL_ROWS_NEEDED, LIMIT_PER_PAGE):
    # Order by incident_number to ensure pagination windows don't overlap data rows
    query_url = f"{API_ENDPOINT}?$limit={LIMIT_PER_PAGE}&$offset={offset}&$order=incident_number"
    try:
        response = requests.get(query_url, timeout=30)
        if response.status_code != 200:
            print(f"API Error at offset {offset}: Status Code {response.status_code}")
            print(f"Details: {response.text}")
            break
        data = response.json()
        if not data:
            print("Reached the end of available API live record rows.")
            break
        all_records.extend(data)
        print(f"Progress Download Layer: {len(all_records)} / {TOTAL_ROWS_NEEDED} entries captured...")
    except requests.exceptions.RequestException as e:
        print(f"Network error encountered at offset {offset}: {e}")
        break
 
# Parse JSON into clean matrix columns
df_raw = pd.DataFrame(all_records)
print(f"Ingestion extraction complete. Constructed shape matrix: {df_raw.shape}")
 
# Validate target field exists before wasting cloud compute uploading an empty shell
if 'priority_level' not in df_raw.columns:
    print("WARNING: 'priority_level' column missing in this batch! Check API fields.")
 
# =====================================================================
# 4. SYNCHRONIZE DATA WITH AWS S3 STORAGE
# =====================================================================
print(f"Streaming dataset into target bucket lake: s3://{BUCKET_NAME}/{MASTER_FILE_KEY}...")
 
try:
    # Build string memory buffer stream to conform with cloud-native deployment rules
    csv_buffer = io.StringIO()
    df_raw.to_csv(csv_buffer, index=False)
    # Put the object into your verified bucket
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=MASTER_FILE_KEY,
        Body=csv_buffer.getvalue()
    )
    print("SUCCESS: Data layer fully synchronized with AWS S3 data lake!")
except session.exceptions.ClientError as ce:
    print(f"AWS Client error during upload: {ce}")
except Exception as e:
    print(f"Failed to synchronize artifact with cloud platform: {e}")
