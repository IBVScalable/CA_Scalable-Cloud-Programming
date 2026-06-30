import io
import time
import json
import boto3
import pandas as pd

# The SDK will automatically resolve credentials natively via the EC2 IAM Role
s3 = boto3.client('s3', region_name="us-east-1")
kinesis = boto3.client('kinesis', region_name="us-east-1")

BUCKET_NAME = "nci-911-austin-project-2026"
INPUT_FILE_KEY = "austin_911_raw_api_data.csv"
STREAM_NAME = "austin_911_stream"

# 1. Ensure Kinesis Stream Exists
try:
    kinesis.describe_stream(StreamName=STREAM_NAME)
    print(f"Connected to existing Kinesis stream: {STREAM_NAME}")
except kinesis.exceptions.ResourceNotFoundException:
    print(f"Creating active Kinesis Stream: {STREAM_NAME}...")
    kinesis.create_stream(StreamName=STREAM_NAME, ShardCount=1)
    time.sleep(5) # Wait for AWS provisioning

# 2. Download and stream data chunks from the data lake
print("Downloading historical reference array from S3 data lake...")
obj = s3.get_object(Bucket=BUCKET_NAME, Key=INPUT_FILE_KEY)
df = pd.read_csv(io.BytesIO(obj['Body'].read())).fillna("UNKNOWN")

print("Starting live pipeline ingestion replay engine (5 records/sec)...")
for index, row in df.iterrows():
    payload = row.to_dict()
    
    # Push record to Kinesis Stream
    kinesis.put_record(
        StreamName=STREAM_NAME,
        Data=json.dumps(payload),
        PartitionKey=str(payload.get('incident_number', time.time()))
    )
    
    if index % 10 == 0:
        print(f"Ingested record sequence count: {index} -> Stream Event: {payload.get('incident_type')}")
        
    time.sleep(0.2) # Throttled pace to simulate real-world arrival frequency