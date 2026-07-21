import boto3
import io
import csv

def stream_combine():
    s3 = boto3.client('s3')
    bucket = 'nci-911-austin-project-2026'
    prefix = 'f1-data/'
    output_key = 'final/master_f1_data_combined.csv'
    
    # We will use a generator to yield rows, preventing RAM overload
    def get_rows():
        paginator = s3.get_paginator('list_objects_v2')
        header_written = False
        
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get('Contents', []):
                if not obj['Key'].endswith('.csv'): continue
                
                print(f"Streaming {obj['Key']}...")
                resp = s3.get_object(Bucket=bucket, Key=obj['Key'])
                reader = csv.reader(io.TextIOWrapper(resp['Body'], encoding='utf-8'))
                
                header = next(reader)
                if not header_written:
                    yield header
                    header_written = True
                
                for row in reader:
                    yield row

    # Streaming upload using a generator as a file-like object
    class GeneratorFile:
        def __init__(self, generator):
            self.gen = generator
            self.buffer = io.StringIO()
            self.writer = csv.writer(self.buffer)
        def read(self, size=-1):
            # This is a basic implementation of a streaming file-like object
            # For massive datasets, consider AWS Glue.
            pass

    # Simplified approach: Use a smaller memory footprint
    with open('combined_stream.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        for row in get_rows():
            writer.writerow(row)
    
    # Upload once at the end
    s3.upload_file('combined_stream.csv', bucket, output_key)

if __name__ == "__main__":
    stream_combine()
