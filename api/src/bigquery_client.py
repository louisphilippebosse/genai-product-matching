# BigQuery integration
from google.cloud import bigquery

def query_bigquery(query):
    client = bigquery.Client(project="genai-product-matching")
    return client.query(query).result()

def get_long_name_by_datapoint_id(datapoint_id):
    """
    Query BigQuery to retrieve the LONG_NAME for a given datapoint_id.
    Args:
        datapoint_id (str): The datapoint ID to query.

    Returns:
        str: The LONG_NAME value for the datapoint_id, or None if not found.
    """
    query = f"""
        SELECT long_name
        FROM `genai-product-matching.embedding_dataset.table_name`
        WHERE id = '{datapoint_id}'
        LIMIT 1
    """
    results = query_bigquery(query)
    for row in results:
        return row.long_name  # Return the LONG_NAME value
    return None  # Return None if no matching datapoint_id is found