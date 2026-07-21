import time
import json
import boto3
import csv
import io
import os
import sys

# 1. Configuration: Get worker count argument for benchmark tracking
workers = sys.argv[1] if len(sys.argv) > 1 else "1"

BUCKET_NAME = "nci-911-austin-project-2026" 
INPUT_FILE_KEY = "final/master_f1_data_combined.csv"

# --- BENCHMARKING START ---
start_time = time.time()

print("Connecting to S3 and streaming 11.5 GB file line-by-line...")
s3_client = boto3.client('s3', region_name="us-east-1")
response = s3_client.get_object(Bucket=BUCKET_NAME, Key=INPUT_FILE_KEY)

text_stream = io.TextIOWrapper(response['Body'], encoding='utf-8')
reader = csv.DictReader(text_stream)

driver_stats = {}
row_count = 0

def save_checkpoint(stats_dict):
    """Helper to dump current aggregates to JSON so the file exists immediately"""
    serving_dict = {}
    for drv, st in stats_dict.items():
        avg_t = st["throttle_sum"] / st["throttle_count"] if st["throttle_count"] > 0 else 0
        avg_r = st["rpm_sum"] / st["rpm_count"] if st["rpm_count"] > 0 else 0
        serving_dict[drv] = {
            "historical_avg_throttle": avg_t,
            "historical_avg_rpm": avg_r
        }
    sorted_dict = dict(sorted(serving_dict.items(), key=lambda item: item[1]["historical_avg_throttle"], reverse=True))
    with open("batch_serving_view.json", "w") as f:
        json.dump(sorted_dict, f, indent=4)

for row in reader:
    driver = row.get("driver_id")
    if not driver:
        continue
    
    try:
        throttle = float(row.get("throttle", 0) or 0)
        rpm = float(row.get("rpm", 0) or 0)
    except ValueError:
        continue  
        
    if driver not in driver_stats:
        driver_stats[driver] = {"throttle_sum": 0.0, "throttle_count": 0, "rpm_sum": 0.0, "rpm_count": 0}
    
    driver_stats[driver]["throttle_sum"] += throttle
    driver_stats[driver]["throttle_count"] += 1
    driver_stats[driver]["rpm_sum"] += rpm
    driver_stats[driver]["rpm_count"] += 1
    
    row_count += 1
    
    # Print progress and save checkpoint every 1 million rows so you see output fast
    if row_count % 1_000_000 == 0:
        print(f"Processed {row_count} rows... saving checkpoint.")
        save_checkpoint(driver_stats)

# Final save upon completion
save_checkpoint(driver_stats)

# --- BENCHMARKING END ---
execution_time = time.time() - start_time

# Append to benchmark_data.csv
file_exists = os.path.isfile('benchmark_data.csv')
with open('benchmark_data.csv', 'a', newline='') as f:
    writer = csv.writer(f)
    if not file_exists:
        writer.writerow(['Workers', 'Execution_Time', 'Ingestion_Rate', 'Latency'])
    writer.writerow([workers, execution_time, 0, 0])

print(f"\nBatch processing finished successfully in {execution_time:.4f} seconds!")