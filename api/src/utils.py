from google.cloud import storage

def load_internal_products_from_gcs(project_id, bucket_name, file_name):
    """
    Load internal products from a file in Google Cloud Storage.
    Args:
        bucket_name (str): The name of the GCS bucket.
        file_name (str): The name of the file in the bucket.

    Returns:
        list: A list of internal product names.
    """
    client = storage.Client(project=project_id)  # Replace with your GCP project ID
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    content = blob.download_as_text()
    return content.splitlines()