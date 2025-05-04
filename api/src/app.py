import os
from flask import Flask, send_from_directory, request, jsonify

app = Flask(__name__, static_folder="../frontend/public")

@app.route("/")
def serve_frontend():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/api")
def api_home():
    return "Welcome to the Product Matching API!"

@app.route("/api/match", methods=["POST"])
def match_product():
    # Get the uploaded file from the request
    file = request.files.get("external")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    # Process the file and perform matching logic
    # Example: matched_product = some_matching_logic(file)
    matched_product = "Example Matched Product"  # Replace with actual logic

    # Return the matched product as a JSON response
    return jsonify({"matchedProduct": matched_product})

if __name__ == "__main__":
    # Bind to the port specified by the PORT environment variable
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)