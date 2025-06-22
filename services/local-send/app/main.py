from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import json
import hashlib
import secrets
from werkzeug.utils import secure_filename
from spake_utils import SPAKE2Handler
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'zip', 'rar'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# In-memory storage for sessions (use Redis in production)
active_sessions = {}
pending_transfers = {}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_session_id():
    """Generate a unique session ID"""
    return secrets.token_hex(8)

def generate_verification_code():
    """Generate a 6-digit verification code"""
    return f"{secrets.randbelow(1000000):06d}"

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/session/create', methods=['POST'])
def create_session():
    """Create a new SPAKE2 session for secure file transfer"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        password = data.get('password', '')
        if not password:
            return jsonify({'error': 'Password required'}), 400
        
        session_id = generate_session_id()
        verification_code = generate_verification_code()
        
        # Initialize SPAKE2 handler
        spake_handler = SPAKE2Handler(password, session_id)
        public_key = spake_handler.generate_public_key()
        
        # Store session
        active_sessions[session_id] = {
            'spake_handler': spake_handler,
            'verification_code': verification_code,
            'created_at': datetime.now(),
            'status': 'waiting_for_peer',
            'files': []
        }
        
        logger.info(f"Created session {session_id}")
        
        return jsonify({
            'session_id': session_id,
            'verification_code': verification_code,
            'public_key': public_key.hex(),
            'status': 'created'
        })
    
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        return jsonify({'error': 'Failed to create session'}), 500

@app.route('/api/session/<session_id>/join', methods=['POST'])
def join_session(session_id):
    """Join an existing SPAKE2 session"""
    try:
        if session_id not in active_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        password = data.get('password', '')
        peer_public_key = data.get('public_key', '')
        verification_code = data.get('verification_code', '')
        
        session = active_sessions[session_id]
        
        # Verify verification code
        if verification_code != session['verification_code']:
            return jsonify({'error': 'Invalid verification code'}), 401
        
        # Complete SPAKE2 key exchange
        try:
            peer_key_bytes = bytes.fromhex(peer_public_key)
            shared_secret = session['spake_handler'].complete_key_exchange(peer_key_bytes)
            session['shared_secret'] = shared_secret
            session['status'] = 'connected'
            
            logger.info(f"Session {session_id} connected successfully")
            
            return jsonify({
                'status': 'connected',
                'public_key': session['spake_handler'].generate_public_key().hex()
            })
        
        except Exception as e:
            logger.error(f"Key exchange failed: {str(e)}")
            return jsonify({'error': 'Key exchange failed'}), 400
    
    except Exception as e:
        logger.error(f"Error joining session: {str(e)}")
        return jsonify({'error': 'Failed to join session'}), 500

@app.route('/api/session/<session_id>/upload', methods=['POST'])
def upload_file(session_id):
    """Upload a file to a session"""
    try:
        if session_id not in active_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        session = active_sessions[session_id]
        if session['status'] != 'connected':
            return jsonify({'error': 'Session not connected'}), 400
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Secure the filename
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{session_id}_{timestamp}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Save file
        file.save(file_path)
        
        # Calculate file hash for integrity verification
        file_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                file_hash.update(chunk)
        
        file_info = {
            'original_name': file.filename,
            'stored_name': unique_filename,
            'file_path': file_path,
            'size': os.path.getsize(file_path),
            'hash': file_hash.hexdigest(),
            'uploaded_at': datetime.now().isoformat()
        }
        
        session['files'].append(file_info)
        
        logger.info(f"File uploaded to session {session_id}: {filename}")
        
        return jsonify({
            'status': 'uploaded',
            'file_id': len(session['files']) - 1,
            'filename': file.filename,
            'size': file_info['size'],
            'hash': file_info['hash']
        })
    
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return jsonify({'error': 'Failed to upload file'}), 500

@app.route('/api/session/<session_id>/files', methods=['GET'])
def list_files(session_id):
    """List files in a session"""
    try:
        if session_id not in active_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        session = active_sessions[session_id]
        if session['status'] != 'connected':
            return jsonify({'error': 'Session not connected'}), 400
        
        files_list = []
        for i, file_info in enumerate(session['files']):
            files_list.append({
                'file_id': i,
                'filename': file_info['original_name'],
                'size': file_info['size'],
                'hash': file_info['hash'],
                'uploaded_at': file_info['uploaded_at']
            })
        
        return jsonify({'files': files_list})
    
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        return jsonify({'error': 'Failed to list files'}), 500

@app.route('/api/session/<session_id>/download/<int:file_id>', methods=['GET'])
def download_file(session_id, file_id):
    """Download a file from a session"""
    try:
        if session_id not in active_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        session = active_sessions[session_id]
        if session['status'] != 'connected':
            return jsonify({'error': 'Session not connected'}), 400
        
        if file_id >= len(session['files']):
            return jsonify({'error': 'File not found'}), 404
        
        file_info = session['files'][file_id]
        
        if not os.path.exists(file_info['file_path']):
            return jsonify({'error': 'File no longer available'}), 404
        
        logger.info(f"File downloaded from session {session_id}: {file_info['original_name']}")
        
        return send_file(
            file_info['file_path'],
            as_attachment=True,
            download_name=file_info['original_name']
        )
    
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return jsonify({'error': 'Failed to download file'}), 500

@app.route('/api/session/<session_id>/status', methods=['GET'])
def session_status(session_id):
    """Get session status"""
    try:
        if session_id not in active_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        session = active_sessions[session_id]
        
        return jsonify({
            'session_id': session_id,
            'status': session['status'],
            'created_at': session['created_at'].isoformat(),
            'file_count': len(session['files'])
        })
    
    except Exception as e:
        logger.error(f"Error getting session status: {str(e)}")
        return jsonify({'error': 'Failed to get session status'}), 500

@app.route('/api/session/<session_id>/close', methods=['POST'])
def close_session(session_id):
    """Close a session and cleanup files"""
    try:
        if session_id not in active_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        session = active_sessions[session_id]
        
        # Cleanup files
        for file_info in session['files']:
            try:
                if os.path.exists(file_info['file_path']):
                    os.remove(file_info['file_path'])
            except Exception as e:
                logger.warning(f"Failed to remove file {file_info['file_path']}: {str(e)}")
        
        # Remove session
        del active_sessions[session_id]
        
        logger.info(f"Session {session_id} closed and cleaned up")
        
        return jsonify({'status': 'closed'})
    
    except Exception as e:
        logger.error(f"Error closing session: {str(e)}")
        return jsonify({'error': 'Failed to close session'}), 500

# Cleanup old sessions periodically (simple implementation)
def cleanup_old_sessions():
    """Remove sessions older than 1 hour"""
    current_time = datetime.now()
    sessions_to_remove = []
    
    for session_id, session in active_sessions.items():
        if current_time - session['created_at'] > timedelta(hours=1):
            sessions_to_remove.append(session_id)
    
    for session_id in sessions_to_remove:
        try:
            # Cleanup files
            session = active_sessions[session_id]
            for file_info in session['files']:
                if os.path.exists(file_info['file_path']):
                    os.remove(file_info['file_path'])
            
            del active_sessions[session_id]
            logger.info(f"Cleaned up expired session: {session_id}")
        except Exception as e:
            logger.error(f"Error cleaning up session {session_id}: {str(e)}")

if __name__ == '__main__':
    # Run cleanup on startup
    cleanup_old_sessions()
    
    # Start Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)