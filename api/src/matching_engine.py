import logging
import time
from google import genai
from google.genai.types import EmbedContentConfig
from google.cloud import aiplatform_v1
from bigquery_client import get_long_name_by_datapoint_id
from langchain.chat_models import init_chat_model
from typing import Optional, List
from pydantic import BaseModel, Field

class ProductSize(BaseModel):
    """Extracted product size information."""
    size: Optional[str] = Field(default=None, description="The size of the product (e.g., '3 OZ', '1lb', '12g').")
    unit: Optional[str] = Field(default=None, description="The unit of measurement (e.g., 'OZ', 'lb', 'g').")

class ProductComparison(BaseModel):
    """Comparison result between uploaded product and possible match."""
    is_confident: bool = Field(default=False, description="Whether the match is confident.")
    reason: Optional[str] = Field(default=None, description="Reason for the confidence decision.")


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize the GenAI client for embedding generation
try:
    genai_client = genai.Client(vertexai=True, project="genai-product-matching", location="northamerica-northeast1")
    logging.info("GenAI client initialized successfully.")
except Exception as e:
    logging.error(f"Failed to initialize GenAI client: {str(e)}")
    raise

# Initialize the Gemini Flash Pro 1.5 model
llm = init_chat_model(
    "gemini-2.0-flash-001",
    model_provider="google_vertexai"
)
import json

def process_semi_confident_matches(uploaded_product, possible_matches):
    """
    Process semi-confident matches using an LLM to determine the most probable match.
    Args:
        uploaded_product (str): The uploaded product name.
        possible_matches (list): List of possible matches (dicts with 'datapoint_id' and 'long_name').

    Returns:
        dict: A confident match if found, or all possible matches if no confident match is determined.
    """
    # Prepare the input for the LLM
    prompt = f"""
        You are an expert in product matching. Your task is to compare the uploaded product with possible matches.
        Extract the product size (e.g., '3 OZ', '1lb', '12g') from both the uploaded product and the possible matches.
        A confident match requires **all key details to match exactly**, including:
        - Product size (e.g., '16oz', '1lb').
        - Flavor (e.g., 'Strawberry Banana', 'Peach Mango').
        - Brand (e.g., 'BodyArmor', 'Lipton').
        - Product line or type (e.g., 'Lyte', 'Diet').

        If there is any difference in these details, it should not be considered a confident match, even if the product size matches.

        Uploaded Product: {uploaded_product}
        Possible Matches: {', '.join([match['long_name'] for match in possible_matches])}

        Here are examples of correct and incorrect matches to guide you:

        #### Correct Matches:
        | External_Product_Name                     | Internal_Product_Name                          |
        |-------------------------------------------|-----------------------------------------------|
        | DIET LIPTON GREEN TEA W/ CITRUS 20 OZ     | Lipton Diet Green Tea with Citrus (20oz)      |
        | CH-CHERRY CHS CLAW DANISH 4.25 OZ         | Cloverhill Cherry Cheese Bearclaw Danish (4.25oz) |

        Reason for Correct Matches:
        - The product size matches exactly.
        - The product name, flavor, brand, and product line are identical or highly similar.

        #### Wrong Matches:
        | External_Product_Name                     | Internal_Product_Name                          |
        |-------------------------------------------|-----------------------------------------------|
        | BodyArmor Strawberry Banana (16oz)        | BodyArmor Lyte Peach Mango (16oz)             |
        | COOKIE PEANUT BUTTER 2OZ                  | Famous Amos Peanut Butter Cookie (2oz)        |

        Reason for Wrong Matches:
        - The product size matches, but the flavor or product line is different (e.g., Strawberry Banana vs Peach Mango).
        - The product size or description does not match (e.g., different flavor, brand, or type).

        Now, compare the uploaded product with the possible matches and return the result as a JSON object with the following format:
        {{
            "is_confident": <true/false>,
            "matched_datapoint_id": <string>,  # The datapoint_id of the matched product
            "reason": <string>
        }}
        """

    # Invoke the LLM
    response = llm.invoke(prompt)

    # Log the raw response for debugging
    logging.debug(f"Raw LLM response: {response.content}")

    # Preprocess the response to remove code block markers
    raw_content = response.content.strip()
    if raw_content.startswith("```") and raw_content.endswith("```"):
        raw_content = raw_content.split("\n", 1)[1].rsplit("\n", 1)[0]

    # Parse the response into the ProductComparison schema
    try:
        data = json.loads(raw_content)
        comp = ProductComparison(**data)
        if comp.is_confident and comp.matched_datapoint_id:
            # Find the matched entry
            match = next(
                (m for m in possible_matches if m["datapoint_id"] == comp.matched_datapoint_id),
                None
            )
            if match:
                return {
                    "uploaded": uploaded_product,
                    "matchedWith": {
                        "datapoint_id": match["datapoint_id"],
                        "long_name": match["long_name"],
                        "reason": comp.reason,
                    }
                }
    except Exception as e:
        logging.error(f"Error parsing LLM response: {e}")
    return None  # No confident match
    
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
                #logging.info(f"Raw response from Matching Engine: {response}")
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
                            # Process semi-confident matches with the LLM
                            logging.info(f"Processing semi-confident matches for product: {product}")
                            result = process_semi_confident_matches(product, semi_confident_matches)
                            if result:
                                matched_products.append(result)
                                logging.info(f"LLM confirmed match: {product}")
                            else:
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