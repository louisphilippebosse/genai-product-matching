import os
from flask import Flask, send_from_directory, request, jsonify
from data_processing import process_uploaded_file

# Set static folder for serving frontend files
static_path = os.path.join(os.path.dirname(__file__), "../frontend/public")
app = Flask(__name__, static_folder=static_path)

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

        # Example: Use the first row for matching
        uploaded_product = df["text"].iloc[0]

        # Example logic for determining match status
        matched_products = [{"uploaded": uploaded_product, "matchedWith": "Product A"}]
        uncertain_matches = [{"uploaded": uploaded_product, "possibleMatches": ["Product B", "Product C"]}]
        no_matches = [{"uploaded": uploaded_product}]

        return jsonify({
            "matchedProducts": matched_products,
            "uncertainMatches": uncertain_matches,
            "noMatches": no_matches
        })

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

# Main entrypoint
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
