import os
from flask import Flask, send_from_directory, request, jsonify
from data_processing import process_uploaded_file
from matching_engine import match_products_with_vector_search
from utils import load_internal_products_from_gcs  # Import the utility function

# Set static folder for serving frontend files
static_path = os.path.join(os.path.dirname(__file__), "../frontend/public")
app = Flask(__name__, static_folder=static_path)

# Load internal products from GCS
PROJECT_ID = "genai-product-matching"  # Replace with your GCP project ID
BUCKET_NAME = "genai-product-matching-data"  # Replace with your GCS bucket name
FILE_NAME = "Data_Internal_cleaned.csv"  # Replace with your file name in GCS
internal_products = load_internal_products_from_gcs(PROJECT_ID ,BUCKET_NAME, FILE_NAME)

# Serve index.html for root path
@app.route("/")
def serve_frontend():
    return send_from_directory(app.static_folder, "index.html")

# Catch-all route for frontend SPA paths (e.g., /about, /dashboard)
@app.route("/<path:path>")
def serve_static_or_index(path):
    file_path = os.path.join(app.static_folder, path)
    if os.path.exists(file_path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, "index.html")

# Example API route
@app.route("/api")
def api_home():
    return "Welcome to the Product Matching API!"

@app.route("/api/match", methods=["POST"])
def match_product():
    file = request.files.get("external")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    try:
        # Process and clean the uploaded file
        df = process_uploaded_file(file)
        external_products = df["text"].tolist()

        # Vertex AI Matching Engine parameters
        vertex_ai_endpoint = "projects/genai-product-matching/locations/northamerica-northeast1/indexEndpoints/product-matching-endpoint-id"
        deployed_index_id = "product-matching-deployment"
        project_id = "genai-product-matching"
        region = "northamerica-northeast1"

        # Call the matching engine
        results = match_products_with_vector_search(
            external_products=external_products,
            vertex_ai_endpoint=vertex_ai_endpoint,
            deployed_index_id=deployed_index_id,
            project_id=project_id,
            region=region
        )

        return jsonify(results)

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

# Main entrypoint
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)