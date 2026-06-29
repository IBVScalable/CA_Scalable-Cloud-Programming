import os
import io
import pandas as pd
import numpy as np
import boto3
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score

# =====================================================================
# 1. INITIALIZATION & DATA FETCH
# =====================================================================
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")

if not all([AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_SESSION_TOKEN]):
    raise ValueError("Missing active AWS environment variables for model training.")

session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    aws_session_token=AWS_SESSION_TOKEN,
    region_name="us-east-1"
)
s3 = session.client('s3')

BUCKET_NAME = "nci-911-austin-project-2026"  
INPUT_FILE_KEY = "austin_911_cleaned_features.csv"

print(f"Downloading feature matrix: s3://{BUCKET_NAME}/{INPUT_FILE_KEY}")
obj = s3.get_object(Bucket=BUCKET_NAME, Key=INPUT_FILE_KEY)
df = pd.read_csv(io.BytesIO(obj['Body'].read()))

# =====================================================================
# 2. FEATURE MATRIX & TARGET ISOLATION
# =====================================================================
# One-Hot Encode categorical columns ('sector', 'incident_type_cleaned')
df_encoded = pd.get_dummies(df, columns=['sector', 'incident_type_cleaned'], drop_first=True)

# Separate features (X) and target label (y)
X = df_encoded.drop(columns=['priority_level'])
y = df_encoded['priority_level']

# Split dataset into 80% Train and 20% Evaluation Test matrix
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
print(f"Data split successfully. Training rows: {X_train.shape[0]} | Test rows: {X_test.shape[0]}")

# =====================================================================
# 3. BASELINE MODEL TRAINING
# =====================================================================
print("Training Baseline Random Forest Multi-Class Classifier...")
model = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)

# =====================================================================
# 4. METRIC EVALUATION PRODUCTION OUTPUT
# =====================================================================
print("\n=== BASELINE MODEL EVALUATION METRICS ===")
y_pred = model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)
print(f"Overall Accuracy: {accuracy * 100:.2f}%\n")
print("Classification Report:")
print(classification_report(y_test, y_pred))
