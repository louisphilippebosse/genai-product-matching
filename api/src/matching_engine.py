import logging
import time
from google import genai
from google.genai.types import EmbedContentConfig
from google.cloud import aiplatform_v1
from bigquery_client import get_long_name_by_datapoint_id


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize the GenAI client for embedding generation
try:
    genai_client = genai.Client(vertexai=True, project="genai-product-matching", location="northamerica-northeast1")
    logging.info("GenAI client initialized successfully.")
except Exception as e:
    logging.error(f"Failed to initialize GenAI client: {str(e)}")
    raise

def generate_embeddings_in_batches(texts, batch_size=250, max_calls_per_minute=5, retries=3, retry_delay=10):
    """
    Generate embeddings for a list of texts in batches, respecting API limits.
    Args:
        texts (list): List of texts to generate embeddings for.
        batch_size (int): Maximum number of texts per batch.
        max_calls_per_minute (int): Maximum number of API calls allowed per minute.
        retries (int): Number of retries for transient errors.
        retry_delay (int): Delay (in seconds) between retries.

    Returns:
        list: A list of embeddings corresponding to the input texts.
    """
    embeddings = []
    failed_batches = []
    failed_batches_file = "failed_batches.json"

    # Calculate the delay needed between API calls to respect the rate limit
    delay_between_calls = 60 / max_calls_per_minute

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
                if "RESOURCE_EXHAUSTED" in str(e):
                    logging.warning(f"Quota exceeded. Retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{retries})")
                    time.sleep(retry_delay)
                else:
                    logging.error(f"Error generating embeddings for batch {i // batch_size + 1}: {str(e)}")
                    if attempt < retries - 1:
                        time.sleep(retry_delay)
                    else:
                        logging.error(f"Failed to generate embeddings for batch {i // batch_size + 1} after {retries} retries.")
                        failed_batches.append(batch)

        # Respect the API rate limit
        if i + batch_size < len(texts):
            logging.info(f"Throttling: Waiting {delay_between_calls} seconds before the next batch...")
            time.sleep(delay_between_calls)

    return embeddings

def match_products_with_vector_search_in_batches(
    external_products, batch_size=250, max_calls_per_minute=5
):
    """
    Match external products to internal products using Vertex AI Matching Engine in batches.
    Args:
        external_products (list): List of external product names.
        batch_size (int): Number of products to process in each batch.
        max_calls_per_minute (int): Maximum number of API calls allowed per minute.

    Returns:
        dict: A dictionary with matched, uncertain, and no matches.
    """
    # Set variables for the current deployed index
    API_ENDPOINT = "8241972.northamerica-northeast1-123728674703.vdb.vertexai.goog"
    INDEX_ENDPOINT = "projects/123728674703/locations/northamerica-northeast1/indexEndpoints/4730925855436439552"
    DEPLOYED_INDEX_ID = "product_matching_deployment"

    # Configure the Vector Search client
    client_options = {"api_endpoint": API_ENDPOINT}
    vector_search_client = aiplatform_v1.MatchServiceClient(client_options=client_options)

    matched_products = []
    uncertain_matches = []
    no_matches = []

    # Calculate the delay needed between API calls to respect the rate limit
    delay_between_calls = 60 / max_calls_per_minute

    try:
        # Process products in batches
        for i in range(0, len(external_products), batch_size):
            batch = external_products[i:i + batch_size]
            logging.info(f"Processing batch {i // batch_size + 1} with {len(batch)} products.")

            try:
                # Generate embeddings for the batch
                logging.info(f"Generating embeddings for batch {i // batch_size + 1}.")
                batch_embeddings = generate_embeddings_in_batches(
                    batch, batch_size=batch_size, max_calls_per_minute=max_calls_per_minute
                )

                # Skip querying if no embeddings were generated
                if not batch_embeddings:
                    continue

                # Build the FindNeighborsRequest
                queries = [
                    aiplatform_v1.FindNeighborsRequest.Query(
                        datapoint=aiplatform_v1.IndexDatapoint(feature_vector=embedding),
                        neighbor_count=10  # Number of nearest neighbors to retrieve
                    )
                    for embedding in batch_embeddings
                ]

                request = aiplatform_v1.FindNeighborsRequest(
                    index_endpoint=INDEX_ENDPOINT,
                    deployed_index_id=DEPLOYED_INDEX_ID,
                    queries=queries,
                    return_full_datapoint=False,
                )

                # Query the Vertex AI Matching Engine
                logging.info(f"Querying Vertex AI Matching Engine for batch {i // batch_size + 1}.")
                response = vector_search_client.find_neighbors(request)
                # Log the raw response for debugging
                logging.info(f"Raw response from Matching Engine: {response}")
                # Inside the loop where neighbors are processed
                for product, query_result in zip(batch, response.nearest_neighbors):
                    if query_result.neighbors:
                        neighbors = query_result.neighbors
                        confident_matches = [
                            {
                                "datapoint_id": n.datapoint.datapoint_id,
                                "long_name": get_long_name_by_datapoint_id(n.datapoint.datapoint_id)
                            }
                            for n in neighbors if n.distance > 0.95
                        ]
                        semi_confident_matches = [
                            {
                                "datapoint_id": n.datapoint.datapoint_id,
                                "long_name": get_long_name_by_datapoint_id(n.datapoint.datapoint_id)
                            }
                            for n in neighbors if 0.7 <= n.distance <= 0.95
                        ][:5]

                        if confident_matches:
                            matched_products.append({"uploaded": product, "matchedWith": confident_matches[0]})
                            logging.info(f"Confident match found for product: {product}")
                        elif semi_confident_matches:
                            uncertain_matches.append({"uploaded": product, "possibleMatches": semi_confident_matches})
                            logging.info(f"Uncertain matches found for product: {product}")
                        else:
                            no_matches.append({"uploaded": product})
                            logging.info(f"No matches found for product: {product}")
                    else:
                        no_matches.append({"uploaded": product})
                        logging.info(f"No neighbors found for product: {product}")
            except Exception as e:
                logging.error(f"Error processing batch {i // batch_size + 1}: {str(e)}")
                for product in batch:
                    no_matches.append({"uploaded": product, "error": str(e)})

            # Respect the API rate limit
            if i + batch_size < len(external_products):
                logging.info(f"Throttling: Waiting {delay_between_calls} seconds before the next batch...")
                time.sleep(delay_between_calls)

        return {
            "matchedProducts": matched_products,
            "uncertainMatches": uncertain_matches,
            "noMatches": no_matches,
        }

    except Exception as e:
        logging.error(f"Failed to match products with Vertex AI Matching Engine: {str(e)}")
        raise