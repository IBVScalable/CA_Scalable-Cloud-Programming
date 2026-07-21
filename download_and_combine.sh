#!/bin/bash

# Configuration
BUCKET="nci-911-austin-project-2026"
PREFIX="f1-data/"
OUTPUT="master_f1_data_combined.csv"

# 1. Get list of files and download them one by one
echo "Downloading and concatenating..."

# Get the first file and include the header
FIRST=true
for key in $(aws s3api list-objects-v2 --bucket $BUCKET --prefix $PREFIX --query 'Contents[*].Key' --output text); do
    if [[ $key == *.csv ]]; then
        echo "Processing $key"
        if [ "$FIRST" = true ]; then
            aws s3 cp s3://$BUCKET/$key - > $OUTPUT
            FIRST=false
        else
            # Skip the header (first line) for subsequent files
            aws s3 cp s3://$BUCKET/$key - | tail -n +2 >> $OUTPUT
        fi
    fi
done

echo "Done! Combined file: $OUTPUT"
