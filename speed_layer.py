import time
import json
from collections import deque
from datetime import datetime, timedelta
from kafka import KafkaConsumer
import csv
import os

# --- CONFIGURATION ---
KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC = "f1-telemetry"  
OUTPUT_FILE = "speed_serving_view.json"
METRICS_FILE = "metrics.json" 
WINDOW_SIZE_SECONDS = 60  # Adjusted for F1 telemetry frequency

# Stores: (timestamp, driver_id, throttle, rpm)
event_window = deque()

def log_benchmark_metrics(workers, ingestion_rate, latency):
    file_exists = os.path.isfile('benchmark_data.csv')
    with open('benchmark_data.csv', 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Workers', 'Ingestion_Rate', 'Latency', 'Execution_Time'])
        writer.writerow([workers, ingestion_rate, latency, 0])
        
print(f"Initializing F1 Telemetry Speed Layer ({WINDOW_SIZE_SECONDS}s window)...")

try:
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=[KAFKA_BROKER],
        auto_offset_reset='earliest',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
except Exception as e:
    print(f"Connection failed: {e}")
    exit(1)

try:
    while True:
        loop_start = time.time()
        now = datetime.now()
        
        # 1. Ingest F1 Data
        records_dict = consumer.poll(timeout_ms=100)
        record_count = 0
        
        if records_dict:
            for partition, messages in records_dict.items():
                for message in messages:
                    # Extracting F1-specific telemetry matching producer payload
                    data = message.value
                    driver_id = str(data.get('driver_id', 'UNKNOWN'))
                    
                    try:
                        throttle = float(data.get('throttle', 0.0) or 0.0)
                        rpm = float(data.get('rpm', 0.0) or 0.0)
                    except (ValueError, TypeError):
                        throttle = 0.0
                        rpm = 0.0
                    
                    event_window.append((now, driver_id, throttle, rpm))
                    record_count += 1

        # 2. Sliding Window Eviction
        expiry_time = now - timedelta(seconds=WINDOW_SIZE_SECONDS)
        while event_window and event_window[0][0] < expiry_time:
            event_window.popleft()

        # 3. Aggregate: Calculate Average Telemetry per Driver
        driver_stats = {}
        for _, d_id, throttle, rpm in event_window:
            if d_id not in driver_stats:
                driver_stats[d_id] = {"throttle_sum": 0.0, "rpm_sum": 0.0, "count": 0}
            
            driver_stats[d_id]["throttle_sum"] += float(throttle)
            driver_stats[d_id]["rpm_sum"] += float(rpm)
            driver_stats[d_id]["count"] += 1

        # Calculate final averages for JSON output
        final_view = {}
        for d_id, stats in driver_stats.items():
            count = stats["count"]
            if count > 0:
                final_view[d_id] = {
                    "avg_throttle": stats["throttle_sum"] / count,
                    "avg_rpm": stats["rpm_sum"] / count
                }
            else:
                final_view[d_id] = {
                    "avg_throttle": 0.0,
                    "avg_rpm": 0.0
                }

        # 4. Metrics & File Writing
        loop_end = time.time()
        latency = (loop_end - loop_start) * 1000 
        
        with open(OUTPUT_FILE, "w") as f:
            json.dump(final_view, f, indent=4)
            
        metrics = {"latency_ms": latency, "active_window_size": len(event_window)}
        with open(METRICS_FILE, "w") as f:
            json.dump(metrics, f)
            
        print(f"[{now.strftime('%H:%M:%S')}] Records: {record_count} | Latency: {latency:.2f}ms | Active Drivers Tracked: {len(final_view)}")

        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nF1 Speed Layer safely detached.")