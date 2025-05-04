from google.cloud import aiplatform

def match_products_with_vector_search(external_products, vertex_ai_endpoint, project_id, region):
    """
    Match external products to internal products using Vertex AI Matching Engine.
    Args:
        external_products (list): List of external product names.
        vertex_ai_endpoint (str): Vertex AI Matching Engine endpoint.
        project_id (str): Google Cloud project ID.
        region (str): Google Cloud region.

    Returns:
        dict: A dictionary with matched, uncertain, and no matches.
    """
    matched_products = []
    uncertain_matches = []
    no_matches = []

    # Initialize Vertex AI client
    aiplatform.init(project=project_id, location=region)
    index_endpoint = aiplatform.MatchingEngineIndexEndpoint(vertex_ai_endpoint)

    for external in external_products:
        # Generate embedding for the external product (use your embedding model)
        external_embedding = generate_embedding(external)  # Replace with your embedding logic

        # Query the Vertex AI Matching Engine
        response = index_endpoint.match(
            deployed_index_id="product-matching-deployment",
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
            elif semi_confident_matches:
                uncertain_matches.append({"uploaded": external, "possibleMatches": semi_confident_matches})
            else:
                no_matches.append({"uploaded": external})
        else:
            no_matches.append({"uploaded": external})

    return {
        "matchedProducts": matched_products,
        "uncertainMatches": uncertain_matches,
        "noMatches": no_matches,
    }