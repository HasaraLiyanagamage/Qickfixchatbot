QuickFix Chatbot (Flask)

This is the QuickFix AI Chatbot service built with Python Flask.
It provides simple, rule-based conversational support to guide users during the booking process.

🚀 Features

RESTful /chat endpoint for message interaction

Rule-based NLP using regex patterns

JSON-based responses (easy Flutter integration)

Flask + CORS setup for cross-origin access

Deployable on Render or Railway (with Gunicorn)

🧱 Project Structure
chatbot/
├── app.py
├── requirements.txt
└── README.md

⚙️ Installation
1. Clone the repository
git clone https://github.com/YOUR_USERNAME/quickfix-chatbot.git
cd quickfix-chatbot

2. Set up Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

3. Install dependencies
pip install -r requirements.txt

🧪 Run Locally
python app.py


The chatbot will run at:

http://127.0.0.1:5005


You can test it using:

curl -X POST http://127.0.0.1:5005/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hi"}'


Expected response:

{"reply": "Hello! I'm QuickFix assistant. How can I help you today?"}


🧰 Tech Stack

Python 3

Flask

Flask-CORS

Gunicorn

Render Hosting

👨‍💻 Author
Hasara Liyanagamage
📧 Email: hasaraliyanagamage27@gmail.com
🔗 GitHub: @HasaraLiyanagamage
