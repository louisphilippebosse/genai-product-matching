import csv
import json
from google.cloud import storage

# Input and output paths
input_csv = "c:\\projects\\genai-product-matching\\data\\processed\\Data_Internal_cleaned.csv"
output_jsonl = "c:\\projects\\genai-product-matching\\data\\processed\\internal_products.jsonl"
bucket_name = "genai-product-matching-data"  # GCS bucket name
gcs_path = "contents/internal_products.jsonl"  # Path in the GCS bucket

# Step 1: Convert CSV to JSONL
def csv_to_jsonl(input_csv, output_jsonl):
    with open(input_csv, mode="r", encoding="utf-8") as csv_file, open(output_jsonl, mode="w", encoding="utf-8") as jsonl_file:
        reader = csv.DictReader(csv_file)
        
        for row in reader:
            # Extract the relevant field for embedding (e.g., LONG_NAME)
            if row.get("LONG_NAME"):
                json_object = {"id": row["NAME"], "embedding": row["LONG_NAME"]}
                jsonl_file.write(json.dumps(json_object) + "\n")
    
    print(f"Data successfully converted to JSONL and saved to {output_jsonl}")

# Step 2: Upload JSONL to GCS
def upload_to_gcs(output_jsonl, bucket_name, gcs_path):
    client = storage.Client(project="genai-product-matching")
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(gcs_path)

    # Upload the JSONL file
    blob.upload_from_filename(output_jsonl)
    print(f"File uploaded to GCS: gs://{bucket_name}/{gcs_path}")

if __name__ == "__main__":
    # Step 1: Convert CSV to JSONL
    csv_to_jsonl(input_csv, output_jsonl)

    # Step 2: Upload JSONL to GCS
    upload_to_gcs(output_jsonl, bucket_name, gcs_path)