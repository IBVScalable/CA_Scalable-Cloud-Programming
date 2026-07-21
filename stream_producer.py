import time
import json
import boto3
import io
import csv
from kafka import KafkaProducer

# --- CONFIGURATION ---
KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC = "f1-telemetry"  
BUCKET_NAME = "nci-911-austin-project-2026"
INPUT_FILE_KEY = "final/master_f1_data_combined.csv"

print(f"Initializing F1 Telemetry Producer node...")
print(f"Targeting Kafka Broker: {KAFKA_BROKER} | Topic: {KAFKA_TOPIC}")

# Initialize Kafka Producer
try:
    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_BROKER],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    print("Producer successfully bound.")
except Exception as e:
    print(f"Failed to initialize producer node: {e}")
    exit(1)

# Stream the dataset line-by-line directly from S3 (Zero Memory Footprint)
try:
    print(f"Connecting to S3 and opening stream for ({INPUT_FILE_KEY})...")
    s3_client = boto3.client('s3', region_name="us-east-1")
    response = s3_client.get_object(Bucket=BUCKET_NAME, Key=INPUT_FILE_KEY)
    
    print("S3 stream established. Parsing CSV rows and pushing to Kafka...")
    text_stream = io.TextIOWrapper(response['Body'], encoding='utf-8')
    reader = csv.DictReader(text_stream)
    
    index = 0
    for row in reader:
        # Safely extract and convert fields, handling potential empty strings or nulls
        try:
            raw_rpm = row.get('maxRPM')
            rpm_val = float(raw_rpm) if raw_rpm not in (None, "", "N/A", "None") else 0.0
        except (ValueError, TypeError):
            rpm_val = 0.0

        try:
            raw_throttle = row.get('aiControlled')
            throttle_val = float(raw_throttle) if raw_throttle not in (None, "", "N/A", "None") else 0.0
        except (ValueError, TypeError):
            throttle_val = 0.0

        payload = {
            "driver_id": str(row.get('driverId', 'UNKNOWN')),
            "throttle": throttle_val,
            "rpm": rpm_val
        }
        
        # Fire event asynchronously to Kafka
        producer.send(KAFKA_TOPIC, value=payload)
        
        # Print progress every 100 records
        if index % 100 == 0:
            print(f"?? [SENT] Record {index} | Driver: {payload['driver_id']} | RPM: {payload['rpm']}")
        
        # Flush buffer periodically
        if index % 50 == 0:
            producer.flush()
            
        # Pace the stream interval
        time.sleep(0.05)
        index += 1

except KeyboardInterrupt:
    print("\nStream producer cleanly disengaged.")
except Exception as e:
    print(f"Error during streaming: {e}")
finally:
    producer.close()