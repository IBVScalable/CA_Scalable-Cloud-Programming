import requests
import pandas as pd
import boto3
import io
 
# 1. Provide temporary AWS Academy credentials 
AWS_ACCESS_KEY = "ASIAR52ZYPAZAPGMIFCP"
AWS_SECRET_KEY = "YK74c/135siQCkG9Uv98U0S2ofGSk8F6x6sJWsuG"
AWS_SESSION_TOKEN = "IQoJb3JpZ2luX2VjEOb//////////wEaCXVzLXdlc3QtMiJHMEUCIFJSJT0vauQ+hCMgAeeRFj/PYntWu8KV6SSGThk46w+uAiEAvV2WGmVwNI44WfaYxmJfb8qgqozOZ6Kn+t3vt6ht2C4qvQIIr///////////ARAAGgwxMzI3OTUzNjU0MjYiDH2Cjx0XcyRNZEYG1SqRAo8bY0ED7Mt6GaOy/3ebP3uQXgVPzOfG4Joev4rjxHJOUtHv9NQSaIBeevDOuEOsnojZYY4tAXH6us5ORf7Gk3cBPP50B44PZnxVCDzPNKPZfGPmrvVOd38eGepVcPiZmlGp6Sn/A1hcajrKRQPl85L3jMXEVo/MwriAiGzioRxhN8EB5imNwr7zVaPkRjDNo5IASv48D7PW9/rb0Mrirt+HcRxZ4+kzAnCTBrxHuupdEyhzRv04EcQc7p1eeGwRWsHRnoJ9jSMTJTJtQJwZee6iOIzDUmZlCzx3RIHUuDn0o2bDmqSIuWFgOSr6WlahWzLJnho8KEQf9Mw/7ZpAN7gy35fVWpYvE/czYurZQ0zpVDDQ44nSBjqdAQV65eXwEFRqbgsxQs9WOZQ58szrAB6PSpC/NKoKx2tDwpaPnuK90eGkOjMA0lP1UwfJjBYcdOweIyz5iMlzH973eHR8Aea3MLj3NoPoUCAoIDf6UpXSIE3oc9ztakuZOnGgmw+InFrtWQnx4/ZHW94NYr1543RtsQgLGJ8T7auNYVs/J4PdVfnaGgBaic5x7qQTHY4dW8ed0QorZW0="
 
# 2. Setup targets
API_ENDPOINT = "https://data.austintexas.gov/resource/e687-fx2y.json"
BUCKET_NAME = "nci-911-austin-project-2026"  # Globally unique bucket name you created in S3
MASTER_FILE_KEY = "austin_911_raw_api_data.csv"
 
# 3. Pull a representative chunk from Socrata via offset pagination
LIMIT_PER_PAGE = 5000
TOTAL_ROWS_NEEDED = 60000
all_records = []
 
print("Streaming rows directly from Austin open data portal API...")
for offset in range(0, TOTAL_ROWS_NEEDED, LIMIT_PER_PAGE):
    query_url = f"{API_ENDPOINT}?$limit={LIMIT_PER_PAGE}&$offset={offset}"
    response = requests.get(query_url)
    if response.status_code != 200:
        print(f"Failed. Status code: {response.status_code}")
        break
    data = response.json()
    if not data:
        break
    all_records.extend(data)
    print(f"Progress: Downloaded {len(all_records)} rows...")
 
# Build base DataFrame
df_raw = pd.DataFrame(all_records)
 
# 4. Stream directly to S3 via memory buffer
session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    aws_session_token=AWS_SESSION_TOKEN,
    region_name="us-east-1"
)
s3 = session.client('s3')
 
csv_buffer = io.StringIO()
df_raw.to_csv(csv_buffer, index=False)
s3.put_object(Bucket=BUCKET_NAME, Key=MASTER_FILE_KEY, Body=csv_buffer.getvalue())
 
print(f"Data layer synchronized. Saved to S3: s3://{BUCKET_NAME}/{MASTER_FILE_KEY}")
