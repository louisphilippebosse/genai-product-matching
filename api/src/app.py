import os
import logging
from flask import Flask, send_from_directory, request, jsonify
from data_processing import process_uploaded_file
from matching_engine import match_products_with_vector_search
from utils import load_internal_products_from_gcs  # Import the utility function

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Set static folder for serving frontend files
static_path = os.path.join(os.path.dirname(__file__), "../frontend/public")
app = Flask(__name__, static_folder=static_path)

# Load internal products from GCS
PROJECT_ID = "genai-product-matching"  # Replace with your GCP project ID
BUCKET_NAME = "genai-product-matching-data"  # Replace with your GCS bucket name
FILE_NAME = "Data_Internal_cleaned.csv"  # Replace with your file name in GCS

try:
    logging.info("Loading internal products from GCS...")
    internal_products = load_internal_products_from_gcs(PROJECT_ID, BUCKET_NAME, FILE_NAME)
    logging.info("Internal products loaded successfully.")
except Exception as e:
    logging.error(f"Failed to load internal products from GCS: {str(e)}")
    internal_products = None

# Serve index.html for root path
@app.route("/")
def serve_frontend():
    logging.info("Serving frontend index.html")
    return send_from_directory(app.static_folder, "index.html")

# Catch-all route for frontend SPA paths (e.g., /about, /dashboard)
@app.route("/<path:path>")
def serve_static_or_index(path):
    file_path = os.path.join(app.static_folder, path)
    if os.path.exists(file_path):
        logging.info(f"Serving static file: {path}")
        return send_from_directory(app.static_folder, path)
    else:
        logging.info(f"Path not found: {path}. Serving index.html instead.")
        return send_from_directory(app.static_folder, "index.html")

# Example API route
@app.route("/api")
def api_home():
    logging.info("API home route accessed.")
    return "Welcome to the Product Matching API!"

@app.route("/api/match", methods=["POST"])
def match_product():
    logging.info("Received request to /api/match")
    file = request.files.get("external")
    if not file:
        logging.warning("No file uploaded in the request.")
        return jsonify({"error": "No file uploaded"}), 400

    try:
        # Process and clean the uploaded file
        logging.info("Processing uploaded file...")
        df = process_uploaded_file(file)
        external_products = df["text"].tolist()
        logging.info(f"Extracted {len(external_products)} products from the uploaded file.")

        # Vertex AI Matching Engine parameters
        vertex_ai_endpoint = "projects/genai-product-matching/locations/northamerica-northeast1/indexEndpoints/8032064382299013120"
        deployed_index_id = "product_matching_deployment"
        project_id = "genai-product-matching"
        region = "northamerica-northeast1"

        # Call the matching engine
        logging.info("Calling the matching engine...")
        results = match_products_with_vector_search(
            external_products=external_products,
            vertex_ai_endpoint=vertex_ai_endpoint,
            deployed_index_id=deployed_index_id,
            project_id=project_id,
            region=region
        )
        logging.info("Matching engine returned results successfully.")
        return jsonify(results)

    except ValueError as e:
        logging.error(f"ValueError occurred: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

# Main entrypoint
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logging.info(f"Starting Flask app on port {port}")
    app.run(host="0.0.0.0", port=port)