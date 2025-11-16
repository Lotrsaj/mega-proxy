from flask import Flask, request, jsonify, abort
import requests
import os

app = Flask(__name__)

# MegaLLM's Base URL (from the documentation)
MEGALLM_BASE_URL = "https://ai.megallm.io/v1"

@app.route("/v1/chat/completions", methods=["POST"])
@app.route("/chat/completions", methods=["POST"]) 
def proxy_request():
    # 1. Get the Janitor.ai API Key from the Authorization header
    api_key = request.headers.get("Authorization")

    if not api_key:
        abort(401, description="API Key not provided in Authorization header.")

    # 2. Extract the JSON body
    try:
        janitor_request_data = request.json
    except Exception:
        abort(400, description="Invalid JSON body.")

    # 3. Define the headers for MegaLLM (using the key from Janitor.ai)
    headers = {
        "Authorization": api_key, 
        "Content-Type": "application/json"
    }
    
    # 4. Define the final MegaLLM endpoint
    megallm_url = f"{MEGALLM_BASE_URL}/chat/completions"

    # 5. Forward the request to MegaLLM
    try:
        response = requests.post(
            megallm_url,
            headers=headers,
            json=janitor_request_data,
            timeout=120 
        )
        
        # 6. Return MegaLLM's response back to Janitor.ai
        return response.content, response.status_code, response.headers.items()

    except requests.exceptions.RequestException as e:
        abort(500, description=f"Proxy error: Failed to connect to MegaLLM: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
  
