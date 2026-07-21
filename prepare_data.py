import kagglehub
import boto3
import os
from pyspark.sql import SparkSession

def prepare_f1_dataset():
    bucket_name = 'nci-911-austin-project-2026'

    # 1. Download F1 Data using kagglehub
    print("Downloading dataset...")
    path = kagglehub.dataset_download("die9orla/formula-1-2020-season-telemetry")
    
    # 2. Upload files to S3 via Boto3 (Bypassing Spark for initial upload)
    s3_client = boto3.client('s3')
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith(".csv"):
                local_path = os.path.join(root, file)
                s3_key = f"f1-data/{file}"
                print(f"Uploading {file} to S3...")
                s3_client.upload_file(local_path, bucket_name, s3_key)

    print("Raw files uploaded. Starting Spark aggregation...")

    # 3. Initialize Spark with explicit configuration overrides
    # We set these in the builder to ensure they exist before the JVM initializes S3A
    spark = SparkSession.builder \
        .appName("CombineF1Data") \
        .config("spark.hadoop.fs.s3a.connection.timeout", "60000") \
        .config("spark.hadoop.fs.s3a.socket.timeout", "60000") \
        .config("spark.hadoop.fs.s3a.connection.establish.timeout", "60000") \
        .config("spark.hadoop.fs.s3a.impl.disable.cache", "true") \
        .getOrCreate()

    # 4. Force override any lingering "60s" strings in the current JVM session
    # This acts as a final safeguard if the Spark builder didn't catch the override
    hadoop_conf = spark.sparkContext._jsc.hadoopConfiguration()
    hadoop_conf.set("fs.s3a.connection.timeout", "60000")
    hadoop_conf.set("fs.s3a.socket.timeout", "60000")
    hadoop_conf.set("fs.s3a.connection.establish.timeout", "60000")

    # 5. Read and Write
    s3_input_path = f"s3a://{bucket_name}/f1-data/*.csv"
    output_path = f"s3a://{bucket_name}/master_f1_data_combined"
    
    print(f"Reading from {s3_input_path}...")
    df = spark.read.option("header", "true").csv(s3_input_path)
    
    print("Writing aggregated data...")
    df.coalesce(1).write.mode("overwrite").option("header", "true").csv(output_path)

    print("Success!")
    spark.stop()

if __name__ == "__main__":
    prepare_f1_dataset()
