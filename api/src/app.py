import os
from flask import Flask, send_from_directory, request, jsonify

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

    # Dummy data for the uploaded product (replace with actual parsing logic)
    uploaded_product = "Uploaded Product X"  # Replace with logic to extract product info from the file

    # Example logic for determining match status
    matched_products = [{"uploaded": uploaded_product, "matchedWith": "Product A"}]  # Replace with actual logic
    uncertain_matches = [
        {"uploaded": uploaded_product, "possibleMatches": ["Product B", "Product C", "Product D"]}
    ]  # Replace with actual logic
    no_matches = [{"uploaded": uploaded_product}]  # Replace with actual logic

    return jsonify({
        "matchedProducts": matched_products,
        "uncertainMatches": uncertain_matches,
        "noMatches": no_matches
    })

# Main entrypoint
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
