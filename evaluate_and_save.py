import os
import io
import pickle
import pandas as pd
import numpy as np
import boto3
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix

# =====================================================================
# 1. FETCH AND RE-TRAIN CLOSURE
# =====================================================================
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")

session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    aws_session_token=AWS_SESSION_TOKEN,
    region_name="us-east-1"
)
s3 = session.client('s3')

BUCKET_NAME = "nci-911-austin-project-2026"  
INPUT_FILE_KEY = "austin_911_cleaned_features.csv"

obj = s3.get_object(Bucket=BUCKET_NAME, Key=INPUT_FILE_KEY)
df = pd.read_csv(io.BytesIO(obj['Body'].read()))

df_encoded = pd.get_dummies(df, columns=['sector', 'incident_type_cleaned'], drop_first=True)
X = df_encoded.drop(columns=['priority_level'])
y = df_encoded['priority_level']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

model = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)

# =====================================================================
# 2. GENERATE CONFUSION MATRIX PLOT
# =====================================================================
print("Generating Confusion Matrix plot...")
cm = confusion_matrix(y_test, y_pred)
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=np.unique(y), yticklabels=np.unique(y))
plt.title('Austin 911 Priority Level Classification - Confusion Matrix')
plt.ylabel('Actual Priority')
plt.xlabel('Predicted Priority')

# Save plot locally
plot_filename = "confusion_matrix.png"
plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
plt.close()
print(f"Plot saved locally as {plot_filename}")

# =====================================================================
# 3. SERIALIZE MODEL & UPLOAD ARTIFACTS TO S3
# =====================================================================
print("Serializing model artifact...")
model_buffer = io.BytesIO()
pickle.dump(model, model_buffer)
model_buffer.seek(0)

# Upload trained model .pkl file to S3
s3.put_object(Bucket=BUCKET_NAME, Key="models/random_forest_baseline.pkl", Body=model_buffer.getvalue())
print(f"SUCCESS: Model artifact pushed to s3://{BUCKET_NAME}/models/random_forest_baseline.pkl")

# Upload confusion matrix visualization to S3 for documentation reference
with open(plot_filename, "rb") as img_file:
    s3.put_object(Bucket=BUCKET_NAME, Key="plots/confusion_matrix.png", Body=img_file.read())
print(f"SUCCESS: Confusion matrix plot pushed to s3://{BUCKET_NAME}/plots/confusion_matrix.png")
