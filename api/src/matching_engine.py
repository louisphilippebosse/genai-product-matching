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

def match_products_with_vector_search_in_batches(
    external_products, vertex_ai_endpoint, deployed_index_id, project_id, region, batch_size=10
):
    """
    Match external products to internal products using Vertex AI Matching Engine in batches.
    Args:
        external_products (list): List of external product names.
        vertex_ai_endpoint (str): Vertex AI Matching Engine endpoint.
        deployed_index_id (str): Deployed index ID for the Matching Engine.
        project_id (str): Google Cloud project ID.
        region (str): Google Cloud region.
        batch_size (int): Number of products to process in each batch.

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

        # Process products in batches
        for i in range(0, len(external_products), batch_size):
            batch = external_products[i:i + batch_size]
            logging.info(f"Processing batch {i // batch_size + 1} with {len(batch)} products.")

            try:
                # Generate embeddings for the batch
                logging.info(f"Generating embeddings for batch {i // batch_size + 1}.")
                batch_embeddings = []
                for product in batch:
                    try:
                        embedding = generate_embedding(product)
                        batch_embeddings.append(embedding)
                    except Exception as e:
                        logging.error(f"Failed to generate embedding for product '{product}': {str(e)}")
                        no_matches.append({"uploaded": product, "error": str(e)})

                # Skip querying if no embeddings were generated
                if not batch_embeddings:
                    continue

                # Query the Vertex AI Matching Engine with the batch embeddings
                logging.info(f"Querying Vertex AI Matching Engine for batch {i // batch_size + 1}.")
                response = index_endpoint.match(
                    deployed_index_id=deployed_index_id,
                    queries=batch_embeddings,
                    num_neighbors=5,
                )

                # Process the responses
                for product, neighbors_response in zip(batch, response):
                    if neighbors_response and neighbors_response.neighbors:
                        neighbors = neighbors_response.neighbors
                        confident_matches = [n.id for n in neighbors if n.distance < 0.1]  # Adjust threshold
                        semi_confident_matches = [n.id for n in neighbors if 0.1 <= n.distance < 0.3]

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

        return {
            "matchedProducts": matched_products,
            "uncertainMatches": uncertain_matches,
            "noMatches": no_matches,
        }

    except Exception as e:
        logging.error(f"Failed to match products with Vertex AI Matching Engine: {str(e)}")
        raise