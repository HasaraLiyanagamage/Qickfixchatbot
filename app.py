"""
QuickFix AI Chatbot Service
Python-based chatbot with NLP capabilities for customer support
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime
import json
import re

app = Flask(__name__)
CORS(app)

# Chatbot Configuration
CHATBOT_CONFIG = {
    'name': 'QuickFix Assistant',
    'version': '1.0.0',
    'languages': ['en', 'si', 'ta']
}

# Service Types
SERVICE_TYPES = [
    'plumbing', 'electrical', 'carpentry', 'painting', 
    'cleaning', 'appliance_repair', 'hvac', 'locksmith'
]

# Intent Patterns
INTENT_PATTERNS = {
    'greeting': [
        r'\b(hi|hello|hey|good morning|good afternoon|good evening)\b',
        r'\bහායි\b', r'\bහෙලෝ\b',  # Sinhala
        r'\bவணக்கம்\b'  # Tamil
    ],
    'emergency': [
        r'\b(emergency|urgent|asap|immediately|quick|fast|help)\b',
        r'\b(leak|flooding|fire|shock|broken|not working)\b',
        r'\bදැන්ම\b', r'\bඉක්මනින්\b',  # Sinhala
        r'\bஉடனடி\b'  # Tamil
    ],
    'booking': [
        r'\b(book|schedule|appointment|need|want|looking for)\b',
        r'\b(technician|plumber|electrician|carpenter)\b',
        r'\bබුකින්\b', r'\bතාක්ෂණික\b',  # Sinhala
        r'\bபதிவு\b'  # Tamil
    ],
    'pricing': [
        r'\b(cost|price|charge|fee|how much|rate)\b',
        r'\bවිය\b', r'\bගාස්තුව\b',  # Sinhala
        r'\bவிலை\b'  # Tamil
    ],
    'status': [
        r'\b(status|where|location|track|eta|arriving)\b',
        r'\bස්ථානය\b',  # Sinhala
        r'\bநிலை\b'  # Tamil
    ],
    'cancel': [
        r'\b(cancel|stop|abort|don\'t want)\b',
        r'\bඅවලංගු\b',  # Sinhala
        r'\bரத்து\b'  # Tamil
    ],
    'complaint': [
        r'\b(complaint|issue|problem|not satisfied|bad|poor)\b',
        r'\bගැටලුව\b',  # Sinhala
        r'\bபிரச்சினை\b'  # Tamil
    ],
    'thanks': [
        r'\b(thank|thanks|appreciate)\b',
        r'\bස්තූතියි\b',  # Sinhala
        r'\bநன்றி\b'  # Tamil
    ]
}

# Response Templates
RESPONSES = {
    'greeting': {
        'en': "Hello! I'm QuickFix Assistant. How can I help you today? 😊\n\nI can help you with:\n• Booking a service\n• Emergency repairs\n• Checking prices\n• Tracking your technician\n• Answering questions",
        'si': "ආයුබෝවන්! මම QuickFix සහායකයා. මට ඔබට අද උදව් කළ හැක්කේ කෙසේද? 😊",
        'ta': "வணக்கம்! நான் QuickFix உதவியாளர். இன்று நான் உங்களுக்கு எப்படி உதவ முடியும்? 😊"
    },
    'emergency': {
        'en': "🚨 I understand this is urgent! Let me help you immediately.\n\nWhat type of emergency service do you need?\n• Plumbing (water leak, pipe burst)\n• Electrical (power failure, short circuit)\n• Locksmith (locked out)\n• Other\n\nPlease share your location so I can find the nearest technician.",
        'si': "🚨 මට තේරෙනවා මේක හදිසියි! මම ඔබට වහාම උදව් කරන්නම්.",
        'ta': "🚨 இது அவசரம் என்று எனக்குப் புரிகிறது! நான் உடனடியாக உங்களுக்கு உதவுகிறேன்."
    },
    'booking': {
        'en': "I'll help you book a service! 📅\n\nWhich service do you need?\n1. Plumbing\n2. Electrical\n3. Carpentry\n4. Painting\n5. Cleaning\n6. Appliance Repair\n7. HVAC\n8. Locksmith\n\nPlease select a number or tell me what you need.",
        'si': "මම ඔබට සේවාවක් වෙන්කරවා ගැනීමට උදව් කරන්නම්! 📅",
        'ta': "நான் உங்களுக்கு சேவையை பதிவு செய்ய உதவுகிறேன்! 📅"
    },
    'pricing': {
        'en': "💰 Our pricing is transparent and fair:\n\n• Base Service Fee: LKR 500-1000\n• Hourly Rate: LKR 1000-2000/hour\n• Emergency Service: +50% surcharge\n• Materials: Actual cost\n\nFinal cost depends on:\n✓ Service type\n✓ Time required\n✓ Materials needed\n✓ Distance traveled\n\nYou'll get an estimate before confirming the booking!",
        'si': "💰 අපගේ මිල ගණන් විනිවිද පෙනෙන සහ සාධාරණ වේ:",
        'ta': "💰 எங்கள் விலை வெளிப்படையானது மற்றும் நியாயமானது:"
    },
    'status': {
        'en': "To check your booking status, please provide:\n• Your booking ID, or\n• Your registered phone number\n\nYou can also track your technician in real-time from the 'My Bookings' section in the app.",
        'si': "ඔබගේ වෙන්කරවා ගැනීමේ තත්ත්වය පරීක්ෂා කිරීමට, කරුණාකර සපයන්න:",
        'ta': "உங்கள் பதிவு நிலையை சரிபார்க்க, தயவுசெய்து வழங்கவும்:"
    },
    'cancel': {
        'en': "I can help you cancel your booking. Please note:\n\n⚠️ Cancellation Policy:\n• Free cancellation: Before technician accepts\n• 50% charge: After acceptance, before arrival\n• Full charge: After technician arrives\n\nPlease provide your booking ID to proceed with cancellation.",
        'si': "මට ඔබගේ වෙන්කරවා ගැනීම අවලංගු කිරීමට උදව් කළ හැකිය.",
        'ta': "உங்கள் பதிவை ரத்து செய்ய நான் உதவ முடியும்."
    },
    'complaint': {
        'en': "I'm sorry to hear you're having an issue. 😔\n\nPlease tell me more about the problem:\n• What went wrong?\n• Booking ID (if applicable)\n• What would you like us to do?\n\nYour feedback helps us improve. A support team member will contact you within 24 hours.",
        'si': "ඔබට ගැටලුවක් ඇති බව දැනගැනීමට කණගාටුයි. 😔",
        'ta': "உங்களுக்கு சிக்கல் இருப்பதைக் கேட்டு வருந்துகிறேன். 😔"
    },
    'thanks': {
        'en': "You're welcome! 😊 Is there anything else I can help you with?\n\nIf you need immediate assistance, just ask!\nFor urgent repairs, say 'emergency'.",
        'si': "ඔබට සාදරයෙන් පිළිගනිමු! 😊",
        'ta': "நல்வரவு! 😊"
    },
    'default': {
        'en': "I'm here to help! I can assist you with:\n\n📱 Booking a service\n🚨 Emergency repairs\n💰 Pricing information\n📍 Tracking your technician\n❓ General questions\n\nWhat would you like to know?",
        'si': "මම උදව් කිරීමට මෙහි සිටිමි!",
        'ta': "நான் உதவ இங்கே இருக்கிறேன்!"
    }
}

# FAQ Database
FAQ_DATABASE = {
    'how to book': {
        'en': "To book a service:\n1. Tap 'Request Service' button\n2. Select service type\n3. Choose location\n4. Select urgency level\n5. Confirm booking\n\nA nearby technician will be matched automatically!",
        'si': "සේවාවක් වෙන්කරවා ගැනීමට:\n1. 'සේවාව ඉල්ලන්න' බොත්තම තට්ටු කරන්න",
        'ta': "சேவையை பதிவு செய்ய:\n1. 'சேவை கோரிக்கை' பொத்தானை அழுத்தவும்"
    },
    'payment methods': {
        'en': "We accept:\n💳 Credit/Debit Cards\n💵 Cash on completion\n📱 Mobile wallets\n🏦 Bank transfer\n\nPayment is due after service completion.",
        'si': "අපි පිළිගන්නවා:\n💳 ක්‍රෙඩිට්/ඩෙබිට් කාඩ්පත්",
        'ta': "நாங்கள் ஏற்றுக்கொள்கிறோம்:\n💳 கிரெடிட்/டெபிட் கார்டுகள்"
    },
    'service areas': {
        'en': "We currently serve:\n📍 Colombo and suburbs\n📍 Gampaha\n📍 Kandy\n📍 Galle\n\nExpanding to more areas soon!",
        'si': "අපි දැනට සේවය කරන්නේ:\n📍 කොළඹ සහ තදාසන්න ප්‍රදේශ",
        'ta': "நாங்கள் தற்போது சேவை செய்கிறோம்:\n📍 கொழும்பு மற்றும் புறநகர்"
    },
    'working hours': {
        'en': "🕐 Service Hours:\n• Regular: 8 AM - 8 PM\n• Emergency: 24/7 available\n\nEmergency services may have additional charges.",
        'si': "🕐 සේවා වේලාවන්:\n• සාමාන්‍ය: පෙ.ව. 8 - ප.ව. 8",
        'ta': "🕐 சேவை நேரம்:\n• வழக்கமான: காலை 8 - மாலை 8"
    }
}

def detect_intent(message):
    """Detect user intent from message"""
    message_lower = message.lower()
    
    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return intent
    
    return 'default'

def detect_language(message):
    """Detect message language (simple heuristic)"""
    # Check for Sinhala Unicode range
    if any('\u0D80' <= char <= '\u0DFF' for char in message):
        return 'si'
    # Check for Tamil Unicode range
    if any('\u0B80' <= char <= '\u0BFF' for char in message):
        return 'ta'
    return 'en'

def extract_service_type(message):
    """Extract service type from message"""
    message_lower = message.lower()
    
    for service in SERVICE_TYPES:
        if service in message_lower or service.replace('_', ' ') in message_lower:
            return service
    
    # Check for common variations
    service_keywords = {
        'plumbing': ['plumber', 'pipe', 'water', 'leak', 'tap', 'sink', 'toilet'],
        'electrical': ['electrician', 'power', 'electricity', 'wiring', 'socket', 'light'],
        'carpentry': ['carpenter', 'wood', 'furniture', 'door', 'window'],
        'painting': ['painter', 'paint', 'wall', 'color'],
        'cleaning': ['clean', 'maid', 'housekeeping'],
        'appliance_repair': ['appliance', 'fridge', 'washing machine', 'ac', 'microwave'],
        'hvac': ['ac', 'air conditioning', 'heating', 'cooling'],
        'locksmith': ['lock', 'key', 'locked out', 'door lock']
    }
    
    for service, keywords in service_keywords.items():
        if any(keyword in message_lower for keyword in keywords):
            return service
    
    return None

def get_response(intent, language='en', context=None):
    """Get appropriate response based on intent and language"""
    if intent in RESPONSES:
        return RESPONSES[intent].get(language, RESPONSES[intent]['en'])
    return RESPONSES['default'].get(language, RESPONSES['default']['en'])

def search_faq(query):
    """Search FAQ database"""
    query_lower = query.lower()
    
    for question, answers in FAQ_DATABASE.items():
        if any(word in query_lower for word in question.split()):
            return answers.get('en', '')
    
    return None

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'QuickFix Chatbot',
        'version': CHATBOT_CONFIG['version'],
        'timestamp': datetime.now().isoformat()
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Main chat endpoint"""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                'error': 'Message is required'
            }), 400
        
        user_message = data['message']
        user_id = data.get('userId', 'anonymous')
        session_id = data.get('sessionId', 'default')
        
        # Detect language and intent
        language = detect_language(user_message)
        intent = detect_intent(user_message)
        
        # Extract entities
        service_type = extract_service_type(user_message)
        
        # Check FAQ first
        faq_response = search_faq(user_message)
        
        # Generate response
        if faq_response:
            bot_response = faq_response
        else:
            bot_response = get_response(intent, language)
        
        # Build response
        response_data = {
            'message': bot_response,
            'intent': intent,
            'language': language,
            'timestamp': datetime.now().isoformat(),
            'sessionId': session_id
        }
        
        # Add extracted entities
        if service_type:
            response_data['serviceType'] = service_type
            response_data['suggestedAction'] = 'book_service'
        
        if intent == 'emergency':
            response_data['priority'] = 'high'
            response_data['suggestedAction'] = 'emergency_booking'
        
        # Log conversation (in production, save to database)
        print(f"[{datetime.now()}] User {user_id}: {user_message}")
        print(f"[{datetime.now()}] Bot: {bot_response}")
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Sorry, I encountered an error. Please try again.'
        }), 500

@app.route('/intents', methods=['GET'])
def get_intents():
    """Get available intents"""
    return jsonify({
        'intents': list(INTENT_PATTERNS.keys()),
        'languages': CHATBOT_CONFIG['languages']
    })

@app.route('/faq', methods=['GET'])
def get_faq():
    """Get FAQ database"""
    return jsonify({
        'faqs': FAQ_DATABASE
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
