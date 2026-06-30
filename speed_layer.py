import time
import json
import boto3
from collections import Counter
from datetime import datetime, timedelta

STREAM_NAME = "austin_911_stream"

# Zero-configuration initialization: Automatically uses EC2's IAM Role instance profile
kinesis = boto3.client('kinesis', region_name="us-east-1")

print(f"Initializing Speed Layer connection to: {STREAM_NAME}")

# Dynamic Shard Discovery to avoid hardcoded ShardId exceptions
try:
    stream_info = kinesis.describe_stream(StreamName=STREAM_NAME)
    active_shard_id = stream_info['StreamDescription']['Shards'][0]['ShardId']
except Exception as e:
    print(f"Error describing stream, falling back to default shard: {e}")
    active_shard_id = 'shardId-000000000000'

response = kinesis.get_shard_iterator(
    StreamName=STREAM_NAME,
    ShardId=active_shard_id,
    ShardIteratorType='LATEST'
)
shard_iterator = response['ShardIterator']

# Sliding window buffer configuration (e.g., local tracked logs)
window_duration = timedelta(minutes=5)
event_window = []

print(f"Speed Layer listening on shard [{active_shard_id}] for streaming events... (Ctrl+C to stop)")
try:
    while True:
        response = kinesis.get_records(ShardIterator=shard_iterator, Limit=10)
        shard_iterator = response['NextShardIterator']
        records = response['Records']
        
        current_time = datetime.now()
        
        if records:
            for record in records:
                data = json.loads(record['Data'])
                incident_type = data.get('incident_type', 'OTHER')
                event_window.append((current_time, incident_type))
            
            # Evict events older than our 5-minute sliding window boundary
            event_window = [evt for evt in event_window if current_time - evt[0] <= window_duration]
            
            # Compute sliding-window aggregate
            counts = Counter([evt[1] for evt in event_window])
            top_incidents = counts.most_common(3)
            
            print(f"[{current_time.strftime('%H:%M:%S')}] FRESHNESS VIEW (Last 5 Mins Rolling Top Categories): {top_incidents}")
            
        time.sleep(1)
except KeyboardInterrupt:
    print("\nSpeed Layer safely spun down.")