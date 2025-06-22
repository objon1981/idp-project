from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from spake_utils import SPAKEServer, SPAKEError
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# In-memory storage for active SPAKE sessions
# In production, use Redis or similar
active_sessions = {}

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "spake"}), 200

@app.route('/spake/initiate', methods=['POST'])
def initiate_spake():
    """
    Initiate SPAKE protocol
    Expected payload: {
        "session_id": "unique_session_identifier",
        "password": "shared_password"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON payload provided"}), 400
        
        session_id = data.get('session_id')
        password = data.get('password')
        
        if not session_id or not password:
            return jsonify({"error": "session_id and password are required"}), 400
        
        # Check if session already exists
        if session_id in active_sessions:
            return jsonify({"error": "Session already exists"}), 409
        
        # Create new SPAKE server instance
        spake_server = SPAKEServer()
        public_key = spake_server.generate_public_key(password)
        
        # Store session
        active_sessions[session_id] = {
            'spake_server': spake_server,
            'status': 'initiated',
            'password': password
        }
        
        logger.info(f"SPAKE session initiated: {session_id}")
        
        return jsonify({
            "session_id": session_id,
            "public_key": public_key.hex(),
            "status": "initiated"
        }), 200
        
    except SPAKEError as e:
        logger.error(f"SPAKE error in initiate: {str(e)}")
        return jsonify({"error": f"SPAKE protocol error: {str(e)}"}), 400
    except Exception as e:
        logger.error(f"Unexpected error in initiate: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/spake/exchange', methods=['POST'])
def exchange_keys():
    """
    Exchange public keys and compute shared secret
    Expected payload: {
        "session_id": "unique_session_identifier",
        "client_public_key": "hex_encoded_client_public_key"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON payload provided"}), 400
        
        session_id = data.get('session_id')
        client_public_key_hex = data.get('client_public_key')
        
        if not session_id or not client_public_key_hex:
            return jsonify({"error": "session_id and client_public_key are required"}), 400
        
        # Check if session exists
        if session_id not in active_sessions:
            return jsonify({"error": "Session not found"}), 404
        
        session = active_sessions[session_id]
        
        if session['status'] != 'initiated':
            return jsonify({"error": "Invalid session status"}), 400
        
        try:
            client_public_key = bytes.fromhex(client_public_key_hex)
        except ValueError:
            return jsonify({"error": "Invalid hex format for client_public_key"}), 400
        
        # Compute shared secret
        spake_server = session['spake_server']
        shared_secret = spake_server.compute_shared_secret(client_public_key)
        
        # Update session status
        session['status'] = 'completed'
        session['shared_secret'] = shared_secret
        
        logger.info(f"SPAKE key exchange completed: {session_id}")
        
        return jsonify({
            "session_id": session_id,
            "shared_secret": shared_secret.hex(),
            "status": "completed"
        }), 200
        
    except SPAKEError as e:
        logger.error(f"SPAKE error in exchange: {str(e)}")
        return jsonify({"error": f"SPAKE protocol error: {str(e)}"}), 400
    except Exception as e:
        logger.error(f"Unexpected error in exchange: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/spake/status/<session_id>', methods=['GET'])
def get_session_status(session_id):
    """Get the status of a SPAKE session"""
    try:
        if session_id not in active_sessions:
            return jsonify({"error": "Session not found"}), 404
        
        session = active_sessions[session_id]
        
        return jsonify({
            "session_id": session_id,
            "status": session['status']
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting session status: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/spake/cleanup/<session_id>', methods=['DELETE'])
def cleanup_session(session_id):
    """Clean up a SPAKE session"""
    try:
        if session_id not in active_sessions:
            return jsonify({"error": "Session not found"}), 404
        
        del active_sessions[session_id]
        
        logger.info(f"SPAKE session cleaned up: {session_id}")
        
        return jsonify({
            "session_id": session_id,
            "message": "Session cleaned up successfully"
        }), 200
        
    except Exception as e:
        logger.error(f"Error cleaning up session: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/spake/sessions', methods=['GET'])
def list_sessions():
    """List all active sessions (for debugging)"""
    try:
        sessions = []
        for session_id, session_data in active_sessions.items():
            sessions.append({
                "session_id": session_id,
                "status": session_data['status']
            })
        
        return jsonify({
            "active_sessions": len(sessions),
            "sessions": sessions
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Method not allowed"}), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting SPAKE service on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)