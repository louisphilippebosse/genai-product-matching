import logging
from google import genai
from google.genai.types import EmbedContentConfig
from google.cloud import aiplatform

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize the GenAI client for embedding generation
try:
    genai_client = genai.Client(vertexai=True, project="genai-product-matching", location="northamerica-northeast1")
    logging.info("GenAI client initialized successfully.")
except Exception as e:
    logging.error(f"Failed to initialize GenAI client: {str(e)}")
    raise

def generate_embedding(text):
    """
    Generate an embedding for the given text using a pre-trained embedding model.
    Args:
        text (str): The text to generate an embedding for.

    Returns:
        list: A list of floats representing the embedding vector.
    """
    try:
        logging.info(f"Generating embedding for text: {text}")
        response = genai_client.models.embed_content(
            model="text-embedding-005",
            contents=[text],
            config=EmbedContentConfig(
                task_type="SEMANTIC_SIMILARITY",  # Task type for semantic similarity
                output_dimensionality=768  # Optional: Specify the dimensionality of the embedding
            )
        )
        embedding = response.embeddings[0].values
        logging.info(f"Successfully generated embedding for text: {text}")
        return embedding
    except Exception as e:
        logging.error(f"Failed to generate embedding for text '{text}': {str(e)}")
        raise

def match_products_with_vector_search(external_products, vertex_ai_endpoint, deployed_index_id, project_id, region):
    """
    Match external products to internal products using Vertex AI Matching Engine.
    Args:
        external_products (list): List of external product names.
        vertex_ai_endpoint (str): Vertex AI Matching Engine endpoint.
        deployed_index_id (str): Deployed index ID for the Matching Engine.
        project_id (str): Google Cloud project ID.
        region (str): Google Cloud region.

    Returns:
        dict: A dictionary with matched, uncertain, and no matches.
    """
    matched_products = []
    uncertain_matches = []
    no_matches = []

    try:
        logging.info("Initializing Vertex AI client.")
        aiplatform.init(project=project_id, location=region)
        index_endpoint = aiplatform.MatchingEngineIndexEndpoint(
            index_endpoint_name=vertex_ai_endpoint
        )
        logging.info("Vertex AI client initialized successfully.")

        for external in external_products:
            try:
                logging.info(f"Processing external product: {external}")
                # Generate embedding for the external product
                external_embedding = generate_embedding(external)

                # Query the Vertex AI Matching Engine
                logging.info(f"Querying Vertex AI Matching Engine for product: {external}")
                response = index_endpoint.match(
                    deployed_index_id=deployed_index_id,
                    queries=[external_embedding],
                    num_neighbors=5,
                )

                # Process the response
                if response and response[0].neighbors:
                    neighbors = response[0].neighbors
                    confident_matches = [n.id for n in neighbors if n.distance < 0.1]  # Adjust threshold
                    semi_confident_matches = [n.id for n in neighbors if 0.1 <= n.distance < 0.3]

                    if confident_matches:
                        matched_products.append({"uploaded": external, "matchedWith": confident_matches[0]})
                        logging.info(f"Confident match found for product: {external}")
                    elif semi_confident_matches:
                        uncertain_matches.append({"uploaded": external, "possibleMatches": semi_confident_matches})
                        logging.info(f"Uncertain matches found for product: {external}")
                    else:
                        no_matches.append({"uploaded": external})
                        logging.info(f"No matches found for product: {external}")
                else:
                    no_matches.append({"uploaded": external})
                    logging.info(f"No neighbors found for product: {external}")

            except Exception as e:
                logging.error(f"Error processing product '{external}': {str(e)}")
                no_matches.append({"uploaded": external, "error": str(e)})

        return {
            "matchedProducts": matched_products,
            "uncertainMatches": uncertain_matches,
            "noMatches": no_matches,
        }

    except Exception as e:
        logging.error(f"Failed to match products with Vertex AI Matching Engine: {str(e)}")
        raise