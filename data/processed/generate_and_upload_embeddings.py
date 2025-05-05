import csv
import json
import uuid
import logging
import time
import os
from google.cloud import storage
from google import genai
from google.genai.types import EmbedContentConfig

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize the GenAI client
try:
    genai_client = genai.Client(vertexai=True, project="genai-product-matching", location="northamerica-northeast1")
    logging.info("GenAI client initialized successfully.")
except Exception as e:
    logging.error(f"Failed to initialize GenAI client: {str(e)}")
    raise

# Input and output paths
input_csv = "c:\\projects\\genai-product-matching\\data\\processed\\Data_Internal_cleaned.csv"
output_jsonl = "c:\\projects\\genai-product-matching\\data\\processed\\internal_products.json"
output_csv = "c:\\projects\\genai-product-matching\\data\\processed\\id_embedding_table.csv"
bucket_name = "genai-product-matching-data"  # GCS bucket name
gcs_path = "contents/internal_products.json"  # Path in the GCS bucket

def save_failed_batches(failed_batches, failed_batches_file="failed_batches.json"):
    """
    Save failed batches to a JSON file, appending to existing ones if the file already exists.
    """
    if os.path.exists(failed_batches_file):
        with open(failed_batches_file, mode="r", encoding="utf-8") as file:
            existing_failed_batches = json.load(file)
    else:
        existing_failed_batches = []

    existing_failed_batches.extend(failed_batches)

    with open(failed_batches_file, mode="w", encoding="utf-8") as file:
        json.dump(existing_failed_batches, file, ensure_ascii=False, indent=4)

    logging.error(f"Failed batches saved to {failed_batches_file}. Consider retrying these batches.")

def exponential_backoff(attempt, base_delay=15, max_delay=300):
    """
    Calculate the delay for exponential backoff with a cap.
    """
    delay = min(base_delay * (2 ** attempt), max_delay)
    logging.info(f"Retrying in {delay} seconds...")
    time.sleep(delay)

def generate_embeddings_in_batches(texts, batch_size=250, retries=5, delay_between_batches=10):
    """
    Generate embeddings for a list of texts in batches with exponential backoff for retries.
    Args:
        texts (list): List of texts to generate embeddings for.
        batch_size (int): Number of texts per batch.
        retries (int): Number of retries for transient errors.
        delay_between_batches (int): Delay (in seconds) between batches to avoid hitting quotas.
    """
    embeddings = []
    failed_batches = []
    failed_batches_file = "failed_batches.json"

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        for attempt in range(retries):
            try:
                logging.info(f"Generating embeddings for batch {i // batch_size + 1} with {len(batch)} texts.")
                response = genai_client.models.embed_content(
                    model="text-embedding-005",
                    contents=batch,
                    config=EmbedContentConfig(
                        task_type="SEMANTIC_SIMILARITY",
                        output_dimensionality=768
                    )
                )
                embeddings.extend([embedding.values for embedding in response.embeddings])
                break  # Exit retry loop on success
            except Exception as e:
                logging.warning(f"Error generating embeddings for batch {i // batch_size + 1}: {str(e)}")
                if attempt < retries - 1:
                    exponential_backoff(attempt)
                else:
                    logging.error(f"Failed to generate embeddings for batch {i // batch_size + 1} after {retries} retries.")
                    failed_batches.append(batch)

        # Wait between batches to avoid hitting quotas
        if i + batch_size < len(texts):
            logging.info(f"Waiting {delay_between_batches} seconds before processing the next batch...")
            time.sleep(delay_between_batches)

    if failed_batches:
        save_failed_batches(failed_batches, failed_batches_file)

    return embeddings

def csv_to_jsonl_and_csv(input_csv, output_jsonl, output_csv, batch_size=250):
    """
    Convert a CSV file to a JSONL file with embeddings and simultaneously create a CSV file with id, embedding, and other columns.
    Args:
        input_csv (str): Path to the input CSV file.
        output_jsonl (str): Path to the output JSONL file.
        output_csv (str): Path to the output CSV file.
        batch_size (int): Number of rows to process in each batch.
    """
    texts = []
    rows = []

    # Read the input CSV and collect LONG_NAME values and rows
    with open(input_csv, mode="r", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            if row.get("LONG_NAME"):
                texts.append(row["LONG_NAME"])
                rows.append(row)
            else:
                logging.warning(f"Skipping row with missing or empty 'LONG_NAME': {row}")

    # Open the JSONL and CSV files for writing
    with open(output_jsonl, mode="a", encoding="utf-8") as jsonl_file, \
         open(output_csv, mode="w", encoding="utf-8", newline="") as csv_file:

        # Write the CSV header
        csv_writer = csv.writer(csv_file)
        header = ["id", "embedding"] + list(rows[0].keys())
        csv_writer.writerow(header)

        # Process the data in batches
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_rows = rows[i:i + batch_size]
            try:
                # Generate embeddings for the current batch
                embeddings = generate_embeddings_in_batches(batch_texts, batch_size=batch_size)

                # Write to both JSONL and CSV files
                for row, embedding in zip(batch_rows, embeddings):
                    unique_id = str(uuid.uuid4())
                    # Write to JSONL
                    json_object = {"id": unique_id, "embedding": embedding}
                    jsonl_file.write(json.dumps(json_object) + "\n")
                    # Write to CSV
                    csv_writer.writerow([unique_id, json.dumps(embedding)] + list(row.values()))

                logging.info(f"Successfully processed and saved batch {i // batch_size + 1}.")
            except Exception as e:
                logging.error(f"Failed to process batch {i // batch_size + 1}: {str(e)}")
def upload_to_gcs(output_jsonl, bucket_name, gcs_path):
    """
    Upload a file to Google Cloud Storage.
    """
    for attempt in range(5):  # Retry up to 5 times
        try:
            client = storage.Client(project="genai-product-matching")
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(gcs_path)
            blob.upload_from_filename(output_jsonl)
            logging.info(f"File uploaded to GCS: gs://{bucket_name}/{gcs_path}")
            break
        except Exception as e:
            logging.warning(f"Error uploading to GCS: {str(e)}")
            if attempt < 4:
                exponential_backoff(attempt)
            else:
                logging.error(f"Failed to upload {output_jsonl} to GCS after multiple retries.")

if __name__ == "__main__":
    # Generate JSONL and CSV files simultaneously
    csv_to_jsonl_and_csv(input_csv, output_jsonl, output_csv, batch_size=250)

    # Upload JSONL to GCS
    upload_to_gcs(output_jsonl, bucket_name, gcs_path)