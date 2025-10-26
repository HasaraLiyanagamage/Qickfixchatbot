from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import os

app = Flask(__name__)
CORS(app)

# --- Simple rule-based chatbot ---
def handle_message(text):
    t = text.lower().strip()
    
    if re.search(r'\b(book|fix|repair|need|help)\b', t):
        if 'plumb' in t:
            return {"reply": "I can help you book a plumber. Please send your address and briefly describe the issue."}
        if 'electr' in t:
            return {"reply": "I can help you book an electrician. Please send your address and briefly describe the issue."}
        return {"reply": "Which service do you need? (plumbing / electrical / handyman / appliance)"}

    if re.search(r'\b(track|where|arriv|eta)\b', t):
        return {"reply": "You can view the technician's live location from your booking page. Which booking ID do you want to check?"}

    if re.search(r'\b(price|cost|fee)\b', t):
        return {"reply": "Estimates vary by service and distance. A typical emergency service starts from LKR 1500. I can give a more accurate estimate after you tell me the service and location."}

    if re.search(r'\b(hi|hello|hey)\b', t):
        return {"reply": "Hello! I'm QuickFix assistant. How can I help you today? You can say 'book plumber' or 'track booking <id>'."}

    return {"reply": "Sorry, I didn't understand. You can say 'book plumber', 'track booking <id>' or 'price for electrician'."}


# --- Chat route ---
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json or {}
    message = data.get('message', '')
    if not message:
        return jsonify({"error": "no message"}), 400
    resp = handle_message(message)
    return jsonify({"reply": resp['reply']})


# --- Health route (optional for Render monitoring) ---
@app.route('/', methods=['GET'])
def health():
    return jsonify({"status": "ok", "message": "QuickFix chatbot is running"})


# --- Run app (Render-compatible) ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5005))
    app.run(host='0.0.0.0', port=port, debug=False)
