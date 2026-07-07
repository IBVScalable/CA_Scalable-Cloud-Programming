import time
import json
import random
from datetime import datetime
from kafka import KafkaProducer

# --- CONFIGURATION ---
KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC = "austin_911_stream"

print(f"Initializing Live Stream Producer node...")
print(f"Targeting Kafka Broker: {KAFKA_BROKER} | Topic: {KAFKA_TOPIC}")

# Initialize Kafka Producer
try:
    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_BROKER],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    print("Producer successfully bound to cluster node. Starting live generation...")
except Exception as e:
    print(f"Failed to initialize producer node: {e}")
    exit(1)

# Sample common emergency incident categories matching your dataset profile
incident_pool = [
    "TRAFFIC COMPLAINT", "MEDICAL EMERGENCY", "BURGLARY", 
    "ASSAULT", "FIRE ALARM", "DISTURBANCE", "SUSPICIOUS VEHICLE"
]

try:
    while True:
        # Construct sample streaming telemetry payload
        payload = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "incident_type": random.choice(incident_pool), # Crucial: This key must match what speed_layer reads
            "priority": random.choice([1, 2, 3]),
            "zip_code": f"787{random.randint(0, 59):02d}"
        }
        
        # Fire event asynchronously to Kafka
        producer.send(KAFKA_TOPIC, value=payload)
        print(f"?? [SENT] {payload['timestamp']} | Event: {payload['incident_type']}")
        
        # Flush stream buffer immediately
        producer.flush()
        
        # Pace the stream interval
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nStream producer cleanly disengaged.")