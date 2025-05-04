from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI

def match_products_with_vector_search(internal_products, external_products, vector_store, reasoning_chain):
    """
    Match external products to internal products using exact matching, vector search, and reasoning.
    Args:
        internal_products (list): List of internal product names.
        external_products (list): List of external product names.
        vector_store (FAISS): Vector store containing internal product embeddings.
        reasoning_chain (LLMChain): LangChain reasoning chain for uncertain matches.

    Returns:
        dict: A dictionary with matched, uncertain, and no matches.
    """
    matched_products = []
    uncertain_matches = []
    no_matches = []

    for external in external_products:
        # Step 1: Exact Matching
        if external in internal_products:
            matched_products.append({"uploaded": external, "matchedWith": external})
            continue

        # Step 2: Vector Search for Confident Matches
        search_results = vector_store.similarity_search_with_score(external, k=5)
        confident_matches = [result[0] for result in search_results if result[1] > 0.9]  # Confidence threshold
        semi_confident_matches = [result[0] for result in search_results if 0.7 < result[1] <= 0.9]

        if confident_matches:
            matched_products.append({"uploaded": external, "matchedWith": confident_matches[0]})
        elif semi_confident_matches:
            # Step 3: Use LangChain for Reasoning
            reasoning_result = reasoning_chain.run(
                uploaded_product=external,
                possible_matches=semi_confident_matches
            )
            if reasoning_result.lower() == "uncertain":
                uncertain_matches.append({"uploaded": external, "possibleMatches": semi_confident_matches})
            else:
                matched_products.append({"uploaded": external, "matchedWith": reasoning_result})
        else:
            # Step 4: No Matches
            no_matches.append({"uploaded": external})

    return {
        "matchedProducts": matched_products,
        "uncertainMatches": uncertain_matches,
        "noMatches": no_matches,
    }