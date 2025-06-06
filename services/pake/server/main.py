from flask import Flask, request, jsonify
from flask_cors import CORS
from pake_utils import create_pake_session, finalize_pake

app = Flask(__name__)
CORS(app)

sessions = {}

@app.route('/init', methods=['POST'])
def init_session():
    data = request.get_json()
    username = data['username']
    password = data['password']

    session, msg = create_pake_session(username, password)
    sessions[username] = session

    return jsonify({'message': msg})

@app.route('/confirm', methods=['POST'])
def confirm_session():
    data = request.get_json()
    username = data['username']
    msg = data['message']

    if username in sessions:
        shared_secret = finalize_pake(sessions[username], msg)
        return jsonify({'shared_secret': shared_secret})
    else:
        return jsonify({'error': 'Session not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
