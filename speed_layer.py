import time
import json
import os
from collections import Counter
from datetime import datetime
from kafka import KafkaConsumer

# --- KAFKA CONFIGURATION ---
KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC = "austin_911_stream"
OUTPUT_FILE = "speed_serving_view.json"

print("Initializing Cumulative Speed Layer Core...")

try:
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=[KAFKA_BROKER],
        auto_offset_reset='latest',  # Read incoming live data
        enable_auto_commit=True,
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    print("Successfully connected to Kafka cluster node.")
except Exception as e:
    print(f"Connection failed: {e}")
    exit(1)

# ?? KEY CHANGE: Direct Counter instead of a time-evicting deque list
session_accumulator = Counter()

print("Speed Layer is actively aggregating stream payloads... (Ctrl+C to halt)")

try:
    while True:
        current_time = datetime.now()
        
        # Poll Kafka for records batches
        records_dict = consumer.poll(timeout_ms=200, max_records=100)
        
        if records_dict:
            for partition, messages in records_dict.items():
                for message in messages:
                    data = message.value
                    incident_type = data.get('incident_type', 'OTHER')
                    
                    # ?? Continuously increment metrics instead of dropping old ones
                    session_accumulator[incident_type] += 1

        # Atomically dump current metrics state to disk view matrix
        try:
            with open(OUTPUT_FILE, "w") as f:
                json.dump(dict(session_accumulator), f, indent=4)
        except Exception as e:
            print(f"Write conflict warning: {e}")
            
        # Console health metrics tracking
        print(f"[{current_time.strftime('%H:%M:%S')}] Global Active Session Total: {sum(session_accumulator.values())}")

        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nProcessing engine safely detached.")