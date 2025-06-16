# main.py
import os, imaplib, email
from flask import Flask

app = Flask(__name__)
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
ROUTING_RULES = os.getenv("ROUTING_RULES", "ocr,json-crack").split(",")

@app.route("/process", methods=["POST"])
def process():
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")
        status, msgs = mail.search(None, "UNSEEN")
        for num in msgs[0].split():
            status, msg_data = mail.fetch(num, '(RFC822)')
            msg = email.message_from_bytes(msg_data[0][1])
            print(f"[Router] '{msg['Subject']}' will be routed to: {ROUTING_RULES}")
        mail.close()
        mail.logout()
        return {"status": "Processed"}, 200
    except Exception as e:
        return {"error": str(e)}, 500
