import pandas as pd
from google.cloud import bigquery

# Define file path and BigQuery details
csv_file_path = "id_embedding_table.csv"
project_id = "genai-product-matching"
dataset_id = "embedding_dataset"
table_id = "embedding"

def push_to_bigquery():
    # Load the CSV file into a DataFrame
    df = pd.read_csv(csv_file_path)

    # Drop the 'embeddings' column
    if 'embeddings' in df.columns:
        df = df.drop(columns=['embeddings'])

    # Initialize BigQuery client
    client = bigquery.Client(project=project_id)

    # Define the table reference
    table_ref = f"{project_id}.{dataset_id}.{table_id}"

    # Push the DataFrame to BigQuery
    job = client.load_table_from_dataframe(df, table_ref, location="northamerica-northeast1")

    # Wait for the job to complete
    job.result()

    print(f"Data successfully uploaded to {table_ref}")

if __name__ == "__main__":
    push_to_bigquery()