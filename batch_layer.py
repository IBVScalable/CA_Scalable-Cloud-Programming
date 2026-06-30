import os
import io
import time
import json
import boto3
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count

# 1. Initialize a Local Spark Session (Task Parallelism Boundary)
print("Initializing PySpark distributed execution context...")
spark = SparkSession.builder \
    .appName("Austin911_Batch_Layer") \
    .master("local[*]") \
    .config("spark.driver.memory", "2g") \
    .getOrCreate()

# 2. Source Parameters
BUCKET_NAME = "nci-911-austin-project-2026"
INPUT_FILE_KEY = "austin_911_raw_api_data.csv"
s3_path = f"s3a://{BUCKET_NAME}/{INPUT_FILE_KEY}"

print(f"Loading full historical archive for comprehensive view calculation...")

# Benchmarking start time
start_time = time.time()

# Resolve credentials or fallback gracefully to native IMDS/IAM profile context via boto3
try:
    # Attempt reading from S3 path assuming cluster configuration
    df = spark.read.csv(s3_path, header=True, inferSchema=True)
except Exception:
    print("S3 direct cluster path unavailable standalone. Sourcing via native IAM instance identity...")
    s3_client = boto3.client('s3', region_name="us-east-1")
    obj = s3_client.get_object(Bucket=BUCKET_NAME, Key=INPUT_FILE_KEY)
    pdf = pd.read_csv(io.BytesIO(obj['Body'].read()))
    df = spark.createDataFrame(pdf)

# 3. Core MapReduce/Aggregation Phase (Phase 2 Requirement)
print("Executing parallel historical aggregation over full history...")
batch_summary = df.groupBy("incident_type") \
                  .agg(count("incident_type").alias("total_historical_count")) \
                  .orderBy(col("total_historical_count").desc())

# Action trigger to force distributed computation graph evaluation
results = batch_summary.collect()
execution_time = time.time() - start_time

print("\n=== BATCH LAYER COMPREHENSIVE HISTORICAL VIEW ===")
for row in results[:5]:
    print(f"Incident Type: {row['incident_type']} | Comprehensive Count: {row['total_historical_count']}")

print(f"\nBatch processing execution completed in: {execution_time:.4f} seconds.")

# 4. Create Memory-Mapped Serving Layer View (Bypassing Hadoop Write Permission Bug)
print("\nExporting serving layer view parameters...")
try:
    # Convert Spark DataFrame rows into a fast-lookup dictionary
    serving_batch_dict = {row['incident_type']: row['total_historical_count'] for row in results}
    
    # Save cache natively to bypass local JVM/Hadoop environment writer constraints
    with open("batch_serving_view.json", "w") as f:
        json.dump(serving_batch_dict, f, indent=4)
    print("SUCCESS: Serving layer baseline view securely cached to 'batch_serving_view.json'")
except Exception as e:
    print(f"Warning caching serving view: {e}")

# Graceful context teardown
spark.stop()
print("Batch context gracefully spun down.")