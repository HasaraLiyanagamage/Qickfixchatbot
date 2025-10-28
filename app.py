from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import os
import json
import random
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Enhanced knowledge base for QuickFix services
KNOWLEDGE_BASE = {
    'services': {
        'plumbing': {
            'keywords': ['plumb', 'pipe', 'leak', 'water', 'drain', 'toilet', 'sink', 'faucet', 'water heater'],
            'responses': [
                "I can help you with plumbing services. What specific issue are you facing?",
                "Our plumbing experts handle leaks, pipe repairs, drainage issues, and installations. What's the problem?",
                "For plumbing emergencies, we provide 24/7 service. Please describe your issue."
            ]
        },
        'electrical': {
            'keywords': ['electr', 'electric', 'power', 'outlet', 'switch', 'wire', 'circuit', 'breaker', 'light'],
            'responses': [
                "I can connect you with certified electricians. What electrical issue are you experiencing?",
                "Our electrical services cover repairs, installations, and emergency power issues. How can I help?",
                "Electrical problems can be urgent. Our technicians are available 24/7. What's wrong?"
            ]
        },
        'handyman': {
            'keywords': ['fix', 'repair', 'install', 'mount', 'assemble', 'hang', 'paint', 'door', 'window'],
            'responses': [
                "Our handyman services cover a wide range of home repairs and installations. What needs fixing?",
                "From furniture assembly to minor repairs, our handymen can help. What service do you need?",
                "We handle various home improvement tasks. Please describe what you need done."
            ]
        },
        'appliance': {
            'keywords': ['appliance', 'fridge', 'washer', 'dryer', 'oven', 'microwave', 'dishwasher', 'repair'],
            'responses': [
                "We repair major home appliances. Which appliance is having issues?",
                "Our technicians service refrigerators, washers, dryers, and other appliances. What's the problem?",
                "Appliance repairs are our specialty. Please specify which appliance needs attention."
            ]
        }
    }
}

# Conversation context tracking
conversation_context = {}

def detect_service_type(message):
    """Enhanced service type detection using keyword matching"""
    message_lower = message.lower()

    for service, data in KNOWLEDGE_BASE['services'].items():
        for keyword in data['keywords']:
            if keyword in message_lower:
                return service

    return None

def get_service_response(service_type, message):
    """Generate contextual response based on service type"""
    if service_type in KNOWLEDGE_BASE['services']:
        responses = KNOWLEDGE_BASE['services'][service_type]['responses']
        return random.choice(responses)

    return "I can help you find the right technician for your needs. What type of service do you require?"

def extract_booking_info(message):
    """Extract potential booking information from message"""
    info = {
        'urgency': None,
        'location': None,
        'contact_time': None,
        'budget': None
    }

    # Detect urgency
    urgent_keywords = ['urgent', 'emergency', 'asap', 'immediately', 'quick', 'fast', 'now']
    if any(word in message.lower() for word in urgent_keywords):
        info['urgency'] = 'high'

    # Extract time preferences
    time_patterns = [
        r'(\d{1,2}:\d{2}\s*(am|pm))',
        r'(morning|afternoon|evening|night)',
        r'(today|tomorrow|tonight)'
    ]

    for pattern in time_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            info['contact_time'] = match.group(1) or match.group(0)
            break

    return info

def handle_message(text):
    """Enhanced message handling with context awareness"""
    user_id = "default_user"  # In production, this should come from authentication
    message_lower = text.lower().strip()

    # Initialize context if not exists
    if user_id not in conversation_context:
        conversation_context[user_id] = {
            'last_service': None,
            'booking_stage': None,
            'extracted_info': {}
        }

    context = conversation_context[user_id]

    # Greeting detection
    if re.search(r'\b(hi|hello|hey|greetings|good\s+(morning|afternoon|evening))\b', message_lower):
        return {
            "reply": "Hello! I'm QuickFix Assistant 🤖. I can help you book emergency home repairs, track technicians, or answer questions about our services. What do you need help with?",
            "context": "greeting"
        }

    # Service booking requests
    if re.search(r'\b(book|schedule|request|need|want|help|fix|repair)\b', message_lower):
        service_type = detect_service_type(text)

        if service_type:
            context['last_service'] = service_type
            context['booking_stage'] = 'service_selected'

            response = get_service_response(service_type, text)
            info = extract_booking_info(text)

            if info['urgency']:
                response += " I see this is urgent - I'll prioritize finding available technicians."

            return {
                "reply": response + " Please provide your address and describe the issue in detail.",
                "context": "booking_started",
                "service": service_type,
                "info": info
            }
        else:
            return {
                "reply": "I can help you with plumbing, electrical work, handyman services, or appliance repairs. Which service do you need?",
                "context": "service_selection"
            }

    # Location and address queries
    if re.search(r'\b(address|location|where|area|street|city)\b', message_lower) or context.get('booking_stage') == 'service_selected':
        context['booking_stage'] = 'location_provided'
        return {
            "reply": "Thank you for providing your location. Our smart matching system will find the nearest available technician. Please describe the specific issue you're facing.",
            "context": "location_received"
        }

    # Tracking requests
    if re.search(r'\b(track|where|status|progress|arriv|eta|when)\b', message_lower):
        return {
            "reply": "To track your booking, please provide your booking ID or the phone number used for the request. You can also view live tracking from your booking details in the app.",
            "context": "tracking"
        }

    # Pricing inquiries
    if re.search(r'\b(price|cost|fee|charge|rate|expensive|budget|afford)\b', message_lower):
        return {
            "reply": "Our pricing depends on the service type, complexity, and your location. Emergency services start from LKR 1,500. For accurate quotes, please describe your specific needs and location. We also offer transparent pricing with no hidden fees.",
            "context": "pricing"
        }

    # Technical support
    if re.search(r'\b(problem|issue|error|bug|not\s+work|broken|fail)\b', message_lower):
        return {
            "reply": "I'm sorry you're experiencing issues. Could you please describe the problem in more detail? You can also contact our support team directly at support@quickfix.lk or call +94 XX XXX XXXX.",
            "context": "support"
        }

    # Cancellation requests
    if re.search(r'\b(cancel|stop|terminate|end)\b', message_lower):
        return {
            "reply": "To cancel a booking, please provide your booking ID or contact details. You can also cancel directly through the app. Cancellations within 1 hour of booking are free.",
            "context": "cancellation"
        }

    # Help and information
    if re.search(r'\b(help|info|information|how|what|guide)\b', message_lower):
        return {
            "reply": "I can help you with: \n• Booking emergency repairs (plumbing, electrical, handyman, appliances)\n• Tracking technician location in real-time\n• Getting price estimates\n• Canceling or modifying bookings\n• General support and questions\n\nWhat would you like to know more about?",
            "context": "help"
        }

    # Default response with context awareness
    if context.get('last_service'):
        return {
            "reply": f"I see you're interested in {context['last_service']} services. How can I help you with that? Please provide more details about your needs.",
            "context": "service_context"
        }

    return {
        "reply": "I'm here to help with your home repair needs! You can say things like:\n• 'I need a plumber for a leaky pipe'\n• 'Track my booking'\n• 'How much does electrical repair cost?'\n• 'Help me book a handyman'\n\nWhat can I assist you with?",
        "context": "default"
    }

# Chat route
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json or {}
    message = data.get('message', '')
    user_id = data.get('user_id', 'default_user')

    if not message:
        return jsonify({"error": "no message"}), 400

    resp = handle_message(message)

    # Store conversation context
    if user_id not in conversation_context:
        conversation_context[user_id] = {}
    conversation_context[user_id]['last_interaction'] = datetime.now().isoformat()

    return jsonify({
        "reply": resp['reply'],
        "context": resp.get('context', 'unknown'),
        "timestamp": datetime.now().isoformat()
    })

# Health route
@app.route('/', methods=['GET'])
def health():
    return jsonify({"status": "ok", "message": "QuickFix Enhanced Chatbot is running"})

# Analytics route (for admin)
@app.route('/analytics', methods=['GET'])
def analytics():
    return jsonify({
        "total_conversations": len(conversation_context),
        "services_requested": {k: 0 for k in KNOWLEDGE_BASE['services'].keys()},
        "uptime": "24/7"
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5005))
    app.run(host='0.0.0.0', port=port, debug=False)
