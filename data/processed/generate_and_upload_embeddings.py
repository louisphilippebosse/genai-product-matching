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

# Initialize the GenAI client with increased timeout
try:
    genai_client = genai.Client(vertexai=True, project="genai-product-matching", location="northamerica-northeast1")
    logging.info("GenAI client initialized successfully.")
except Exception as e:
    logging.error(f"Failed to initialize GenAI client: {str(e)}")
    raise

# Input and output paths
input_csv = "c:\\projects\\genai-product-matching\\data\\processed\\Data_Internal_cleaned.csv"
output_jsonl = "c:\\projects\\genai-product-matching\\data\\processed\\internal_products.jsonl"
bucket_name = "genai-product-matching-data"  # GCS bucket name
gcs_path = "embeddings/internal_products.jsonl"  # Path in the GCS bucket

def save_failed_batches(failed_batches, failed_batches_file="failed_batches.json"):
    """
    Save failed batches to a JSON file, appending to existing ones if the file already exists.
    Args:
        failed_batches (list): List of failed batches to save.
        failed_batches_file (str): Path to the file where failed batches are saved.
    """
    # Check if the file already exists
    if os.path.exists(failed_batches_file):
        # Load existing failed batches
        with open(failed_batches_file, mode="r", encoding="utf-8") as file:
            existing_failed_batches = json.load(file)
    else:
        existing_failed_batches = []

    # Append new failed batches to the existing ones
    existing_failed_batches.extend(failed_batches)

    # Save the combined list back to the file
    with open(failed_batches_file, mode="w", encoding="utf-8") as file:
        json.dump(existing_failed_batches, file, ensure_ascii=False, indent=4)

    logging.error(f"Failed batches saved to {failed_batches_file}. Consider retrying these batches.")

def generate_embeddings_in_batches(texts, batch_size=250, delay=20, retries=3, retry_delay=10):
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
                    logging.info(f"Retrying batch {i // batch_size + 1} in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logging.error(f"Failed to generate embeddings for batch {i // batch_size + 1} after {retries} retries.")
                    failed_batches.append(batch)

        if i + batch_size < len(texts):
            logging.info(f"Throttling: Waiting {delay} seconds before the next batch...")
            time.sleep(delay)

    # Save failed batches to a file
    if failed_batches:
        save_failed_batches(failed_batches, failed_batches_file)

    return embeddings

# Step 2: Convert CSV to JSONL with Batched Embeddings
def csv_to_jsonl(input_csv, output_jsonl, batch_size=250, delay=12):
    texts = []
    rows = []

    # Read the CSV and collect texts and rows
    with open(input_csv, mode="r", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            if row.get("LONG_NAME"):
                texts.append(row["LONG_NAME"])
                rows.append(row)
            else:
                logging.warning(f"Skipping row with missing or empty 'LONG_NAME': {row}")

    # Open the JSONL file for writing
    with open(output_jsonl, mode="a", encoding="utf-8") as jsonl_file:
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_rows = rows[i:i + batch_size]
            try:
                # Generate embeddings for the current batch
                embeddings = generate_embeddings_in_batches(batch_texts, batch_size=batch_size, delay=delay)

                # Write the embeddings to the JSONL file
                for row, embedding in zip(batch_rows, embeddings):
                    unique_id = str(uuid.uuid4())
                    json_object = {"id": unique_id, "embedding": embedding}
                    jsonl_file.write(json.dumps(json_object) + "\n")

                logging.info(f"Successfully processed and saved batch {i // batch_size + 1} to {output_jsonl}.")
            except Exception as e:
                logging.error(f"Failed to process batch {i // batch_size + 1}: {str(e)}")

# Step 3: Upload JSONL to GCS
def upload_to_gcs(output_jsonl, bucket_name, gcs_path):
    client = storage.Client(project="genai-product-matching")
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(gcs_path)
    blob.upload_from_filename(output_jsonl)
    logging.info(f"File uploaded to GCS: gs://{bucket_name}/{gcs_path}")

def retry_failed_batches(failed_batches_file="failed_batches.json", new_failed_batches_file="new_failed_batches.json", output_jsonl="internal_products.jsonl", retries=3, retry_delay=10):
    """
    Retry processing the failed batches and save any newly failed batches to a new file.
    Args:
        failed_batches_file (str): Path to the file containing the failed batches.
        new_failed_batches_file (str): Path to the file where newly failed batches will be saved.
        output_jsonl (str): Path to the JSONL file where embeddings will be appended.
        retries (int): Number of retries for each batch.
        retry_delay (int): Delay (in seconds) between retries.
    """
    # Load failed batches
    if not os.path.exists(failed_batches_file):
        logging.error(f"No failed batches file found at {failed_batches_file}. Nothing to retry.")
        return

    with open(failed_batches_file, mode="r", encoding="utf-8") as file:
        failed_batches = json.load(file)

    logging.info(f"Loaded {len(failed_batches)} failed batches from {failed_batches_file}.")

    # Initialize list for newly failed batches
    new_failed_batches = []

    # Open the JSONL file in append mode
    with open(output_jsonl, mode="a", encoding="utf-8") as jsonl_file:
        # Retry each failed batch
        for i, batch in enumerate(failed_batches, start=1):
            for attempt in range(retries):
                try:
                    logging.info(f"Retrying failed batch {i}/{len(failed_batches)} with {len(batch)} texts.")
                    response = genai_client.models.embed_content(
                        model="text-embedding-005",
                        contents=batch,
                        config=EmbedContentConfig(
                            task_type="SEMANTIC_SIMILARITY",
                            output_dimensionality=768
                        )
                    )
                    # Write the embeddings to the JSONL file
                    for embedding in response.embeddings:
                        unique_id = str(uuid.uuid4())
                        json_object = {"id": unique_id, "embedding": embedding.values}
                        jsonl_file.write(json.dumps(json_object) + "\n")

                    logging.info(f"Successfully processed failed batch {i}.")
                    break
                except Exception as e:
                    logging.warning(f"Error processing failed batch {i}: {str(e)}")
                    if attempt < retries - 1:
                        logging.info(f"Retrying failed batch {i} in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    else:
                        logging.error(f"Failed to process failed batch {i} after {retries} retries.")
                        new_failed_batches.append(batch)

    # Save newly failed batches to a new file
    if new_failed_batches:
        with open(new_failed_batches_file, mode="w", encoding="utf-8") as file:
            json.dump(new_failed_batches, file, ensure_ascii=False, indent=4)
        logging.error(f"Newly failed batches saved to {new_failed_batches_file}.")
    else:
        logging.info("All failed batches were successfully retried.")

    # Re-upload the updated JSONL file to GCS
    logging.info(f"Re-uploading {output_jsonl} to GCS...")
    upload_to_gcs(output_jsonl, bucket_name, gcs_path)
    
if __name__ == "__main__":
    #csv_to_jsonl(input_csv, output_jsonl, batch_size=250, delay=12)
    #upload_to_gcs(output_jsonl, bucket_name, gcs_path)
    # Step 3: Retry failed batches
    retry_failed_batches(failed_batches_file="failed_batches.json", new_failed_batches_file="new_failed_batches.json", retries=3, retry_delay=10)