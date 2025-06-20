# main.py
import os, imaplib, email
from flask import Flask, jsonify, request
from datetime import datetime

app = Flask(__name__)
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
ROUTING_RULES = os.getenv("ROUTING_RULES", "ocr,json-crack").split(",")

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({
        "service": "email-router-service",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "routing_rules": ROUTING_RULES
    }), 200

@app.route("/process", methods=["POST"])
def process():
    try:
        if not EMAIL_USER or not EMAIL_PASS:
            return jsonify({
                "status": "Demo Mode",
                "message": "Email credentials not configured. Service running in demo mode.",
                "routing_rules": ROUTING_RULES,
                "timestamp": datetime.now().isoformat()
            }), 200
            
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")
        status, msgs = mail.search(None, "UNSEEN")
        
        processed_emails = []
        for num in msgs[0].split():
            status, msg_data = mail.fetch(num, '(RFC822)')
            msg = email.message_from_bytes(msg_data[0][1])
            processed_emails.append({
                "subject": msg['Subject'],
                "from": msg['From'],
                "routed_to": ROUTING_RULES
            })
            print(f"[Router] '{msg['Subject']}' will be routed to: {ROUTING_RULES}")
            
        mail.close()
        mail.logout()
        
        return jsonify({
            "status": "Processed",
            "emails_processed": len(processed_emails),
            "emails": processed_emails,
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            "status": "Error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route("/test", methods=["POST"])
def test_routing():
    """Test endpoint for document routing simulation"""
    data = request.get_json() or {}
    document_type = data.get("document_type", "unknown")
    filename = data.get("filename", "test_document.pdf")
    
    # Simulate routing logic
    routing_decision = []
    if "pdf" in filename.lower() or document_type == "pdf":
        routing_decision.append("ocr-service")
    if "json" in filename.lower() or document_type == "json":
        routing_decision.append("json-crack")
    if not routing_decision:
        routing_decision = ROUTING_RULES
    
    return jsonify({
        "status": "Routed",
        "filename": filename,
        "document_type": document_type,
        "routed_to": routing_decision,
        "timestamp": datetime.now().isoformat()
    }), 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
