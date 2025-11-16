import os
from flask import Flask, request, Response
import requests

# The base URL for the MegaLLM API endpoint
# Note: You may need to adjust the path here if the MegaLLM documentation
# specifies a different one, but for Anthropic models via MegaLLM, 
# this is usually the correct path.
MEGALLM_BASE_URL = "https://megallm.io/v1/chat/completions"

# Initialize the Flask application
app = Flask(__name__)

# --- ROUTES ---
# We are listening on THREE possible routes to maximize compatibility:
# 1. The base path "/" (to catch the request that was causing the 404)
# 2. /chat/completions (A common path for proxy APIs)
# 3. /v1/chat/completions (The standard OpenAI-compatible path)
@app.route("/", methods=["POST"])
@app.route("/chat/completions", methods=["POST"])
@app.route("/v1/chat/completions", methods=["POST"])
def proxy_request():
    """
    Handles the incoming request from Janitor.ai, forwards it to MegaLLM, 
    and streams the response back.
    """
    try:
        # 1. Extract the API Key from the Authorization header 
        # Janitor.ai sends the key in the Authorization header (e.g., "Bearer sk-...")
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            # Fallback if no Authorization header is found (unlikely but safe)
            return Response("Authorization header not found. Please ensure your API Key is set in Janitor.ai.", status=401)

        # 2. Prepare headers for the MegaLLM request
        # We preserve the existing Authorization header from Janitor.ai
        headers = {
            "Content-Type": "application/json",
            "Authorization": auth_header 
        }

        # 3. Forward the request to MegaLLM
        # We forward the entire request body (the JSON payload)
        # We use stream=True to handle real-time response from the LLM
        megallm_response = requests.post(
            MEGALLM_BASE_URL,
            headers=headers,
            data=request.data,
            stream=True
        )

        # 4. Define a generator function to stream the content back
        def generate():
            for chunk in megallm_response.iter_content(chunk_size=None):
                yield chunk
        
        # 5. Return the response to Janitor.ai (streaming)
        # We preserve the original status code and content type from MegaLLM
        return Response(
            generate(),
            status=megallm_response.status_code,
            content_type=megallm_response.headers.get("Content-Type", "application/json")
        )

    except requests.exceptions.RequestException as e:
        # Handle network or request-related errors
        print(f"MegaLLM Request Error: {e}")
        return Response(f"Proxy failed to connect to MegaLLM: {e}", status=503)
        
    except Exception as e:
        # Handle other unexpected errors
        print(f"Internal Proxy Error: {e}")
        return Response(f"Internal Proxy Error: {e}", status=500)

if __name__ == "__main__":
    # Note: Render/Gunicorn handles this for you, but keep for local testing
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))

