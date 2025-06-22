from flask import Flask, request, jsonify
import json
import requests

app = Flask(__name__)

# Mapping of keyword in payload to microservice URL
SERVICE_ROUTES = {
    "file_path": "http://localhost:5050/send",            # local-send
    "organize": "http://localhost:6060/organize",         # local-file-organizer
    "extract": "http://localhost:7071/extract",           # docetl
    "llm_prompt": "http://localhost:11434/ask",           # anything-llm via ollama
    "email": "http://localhost:5555/route",               # email-router
    "spake_token": "http://localhost:5000/auth",          # spake
    "ocr": "http://localhost:8080/ocr",                   # ocr-service
    "workflow": "http://localhost:9090/start",            # hybrid kestra-windmill
    "kafka_event": "http://localhost:8181/kafka/produce"  # kafka-zookeeper
}

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Welcome to JSON Crack Visualizer Service with Routing"})

@app.route('/visualize', methods=['POST'])
def visualize_and_route():
    try:
        payload = request.get_json(force=True)
        formatted_json = json.dumps(payload, indent=2)

        # Auto-detect service based on keys
        matched_service = None
        for key in payload:
            if key in SERVICE_ROUTES:
                matched_service = key
                break

        if matched_service:
            target_url = SERVICE_ROUTES[matched_service]
            try:
                service_response = requests.post(target_url, json=payload)
                service_data = service_response.json()
            except Exception as e:
                service_data = {"error": f"Failed to contact {matched_service} service", "details": str(e)}
        else:
            service_data = {"note": "No matching microservice found for provided JSON keys."}

        return jsonify({
            "formatted_json": formatted_json,
            "matched_service": matched_service or "none",
            "service_response": service_data
        })

    except Exception as e:
        return jsonify({"error": f"Invalid JSON: {str(e)}"}), 400

if __name__ == '__main__':
    print("🔍 Starting JSON Crack Visualizer Router on port 7070...")
    app.run(host='0.0.0.0', port=7070, debug=True)
