# BigQuery integration
from google.cloud import bigquery

def query_bigquery(query):
    client = bigquery.Client()
    return client.query(query).result()
