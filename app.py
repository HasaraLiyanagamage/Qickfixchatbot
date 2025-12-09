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
import requests
try:
    import nltk
    from nltk.tokenize import word_tokenize
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    NLTK_AVAILABLE = True
    # Download required NLTK data (only first time)
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        nltk.download('wordnet', quiet=True)
except ImportError:
    NLTK_AVAILABLE = False
    print("NLTK not available, using basic NLP")

app = Flask(__name__)
CORS(app)

# Chatbot Configuration
CHATBOT_CONFIG = {
    'name': 'QuickFix Assistant',
    'version': '2.0.0',
    'languages': ['en', 'si', 'ta'],
    'features': ['NLP', 'Multi-language', 'Context-aware', 'Booking Integration']
}

# Conversation Context Storage (in-memory, use Redis/DB in production)
conversation_contexts = {}

# Backend API Configuration
BACKEND_URL = os.environ.get('BACKEND_URL', 'https://quickfix-backend-6ztz.onrender.com')

# Service Types
SERVICE_TYPES = [
    'plumbing', 'electrical', 'carpentry', 'painting', 
    'cleaning', 'appliance_repair', 'hvac', 'locksmith'
]

# Intent Patterns
INTENT_PATTERNS = {
    'greeting': [
        r'\b(hi|hello|hey|good morning|good afternoon|good evening|greetings)\b',
        r'\bහායි\b', r'\bහෙලෝ\b',  # Sinhala
        r'\bவணக்கம்\b'  # Tamil
    ],
    'emergency': [
        r'\b(emergency|urgent|asap|immediately|quick|fast|help|sos)\b',
        r'\b(leak|flooding|fire|shock|broken|not working|burst)\b',
        r'\bදැන්ම\b', r'\bඉක්මනින්\b',  # Sinhala
        r'\bஉடனடி\b'  # Tamil
    ],
    'booking': [
        r'\b(book|schedule|appointment|need|want|looking for|hire|get)\b',
        r'\b(technician|plumber|electrician|carpenter|service)\b',
        r'\bබුකින්\b', r'\bතාක්ෂණික\b',  # Sinhala
        r'\bபதிவு\b'  # Tamil
    ],
    'pricing': [
        r'\b(cost|price|charge|fee|how much|rate|expensive|cheap|afford)\b',
        r'\bවිය\b', r'\bගාස්තුව\b',  # Sinhala
        r'\bவிலை\b'  # Tamil
    ],
    'payment': [
        r'\b(payment|pay|paid|paying|invoice|receipt|refund)\b',
        r'\b(cash|card|credit|debit|wallet|bank transfer)\b',
        r'\bගෙවීම\b',  # Sinhala
        r'\bசெலுத்துதல்\b'  # Tamil
    ],
    'status': [
        r'\b(status|where|location|track|eta|arriving|progress)\b',
        r'\bස්ථානය\b',  # Sinhala
        r'\bநிலை\b'  # Tamil
    ],
    'cancel': [
        r'\b(cancel|stop|abort|don\'t want|remove|delete)\b',
        r'\bඅවලංගු\b',  # Sinhala
        r'\bரத்து\b'  # Tamil
    ],
    'complaint': [
        r'\b(complaint|issue|problem|not satisfied|bad|poor|disappointed|unhappy)\b',
        r'\bගැටලුව\b',  # Sinhala
        r'\bபிரச்சினை\b'  # Tamil
    ],
    'rating': [
        r'\b(rate|rating|review|feedback|stars|recommend)\b',
        r'\bමිණුම\b',  # Sinhala
        r'\bமதிப்பீடு\b'  # Tamil
    ],
    'thanks': [
        r'\b(thank|thanks|appreciate|grateful)\b',
        r'\bස්තූතියි\b',  # Sinhala
        r'\bநன்றி\b'  # Tamil
    ]
}

# Response Templates
RESPONSES = {
    'greeting': {
        'en': "Hello! I'm QuickFix Assistant. How can I help you today? \n\nI can help you with:\n• Booking a service\n• Emergency repairs\n• Checking prices\n• Tracking your technician\n• Answering questions",
        'si': "ආයුබෝවන්! මම QuickFix සහායකයා. මට ඔබට අද උදව් කළ හැක්කේ කෙසේද?\n\nමට ඔබට උදව් කළ හැක්කේ:\n• සේවාවක් වෙන්කරවා ගැනීම\n• හදිසි අලුත්වැඩියා\n• මිල ගණන් පරීක්ෂා කිරීම\n• ඔබේ කාර්මික ශිල්පියා ලුහුබැඳීම\n• ප්‍රශ්න වලට පිළිතුරු දීම",
        'ta': "வணக்கம்! நான் QuickFix உதவியாளர். இன்று நான் உங்களுக்கு எப்படி உதவ முடியும்?\n\nநான் உங்களுக்கு உதவ முடியும்:\n• சேவையை பதிவு செய்தல்\n• அவசர பழுதுபார்ப்பு\n• விலைகளை சரிபார்த்தல்\n• உங்கள் தொழில்நுட்ப வல்லுநரைக் கண்காணித்தல்\n• கேள்விகளுக்கு பதிலளித்தல்"
    },
    'emergency': {
        'en': "I understand this is urgent! Let me help you immediately.\n\nWhat type of emergency service do you need?\n• Plumbing (water leak, pipe burst)\n• Electrical (power failure, short circuit)\n• Locksmith (locked out)\n• Other\n\nPlease share your location so I can find the nearest technician.",
        'si': " මට තේරෙනවා මේක හදිසියි! මම ඔබට වහාම උදව් කරන්නම්.\n\nඔබට අවශ්‍ය හදිසි සේවාව කුමක්ද?\n• ජල නළ (ජල කාන්දුවීම, පයිප්ප පුපුරා යාම)\n• විදුලි (විදුලිය නැතිවීම, කෙටි පරිපථයක්)\n• අගුළු (අගුළු වැටී ඇත)\n• වෙනත්\n\nකරුණාකර ඔබේ ස්ථානය බෙදා ගන්න, මට ආසන්නතම කාර්මික ශිල්පියා සොයා ගත හැකිය.",
        'ta': " இது அவசரம் என்று எனக்குப் புரிகிறது! நான் உடனடியாக உங்களுக்கு உதவுகிறேன்.\n\nஉங்களுக்கு என்ன வகையான அவசர சேவை தேவை?\n• குழாய் (நீர் கசிவு, குழாய் வெடிப்பு)\n• மின்சாரம் (மின்சாரம் தோல்வி, குறுகிய சுற்று)\n• பூட்டு (பூட்டப்பட்டது)\n• மற்றவை\n\nதயவுசெய்து உங்கள் இருப்பிடத்தைப் பகிரவும், நான் அருகிலுள்ள தொழில்நுட்ப வல்லுநரைக் கண்டுபிடிக்க முடியும்."
    },
    'booking': {
        'en': "I'll help you book a service! \n\nWhich service do you need?\n1. Plumbing\n2. Electrical\n3. Carpentry\n4. Painting\n5. Cleaning\n6. Appliance Repair\n7. HVAC\n8. Locksmith\n\nPlease select a number or tell me what you need.",
        'si': "මම ඔබට සේවාවක් වෙන්කරවා ගැනීමට උදව් කරන්නම්!\n\nඔබට අවශ්‍ය සේවාව කුමක්ද?\n1. ජල නළ\n2. විදුලි\n3. වඩු වැඩ\n4. පින්තාරු කිරීම\n5. පිරිසිදු කිරීම\n6. උපකරණ අලුත්වැඩියා\n7. වායු සමීකරණය\n8. අගුළු\n\nකරුණාකර අංකයක් තෝරන්න හෝ ඔබට අවශ්‍ය දේ මට කියන්න.",
        'ta': "நான் உங்களுக்கு சேவையை பதிவு செய்ய உதவுகிறேன்!\n\nஉங்களுக்கு என்ன சேவை தேவை?\n1. குழாய்\n2. மின்சாரம்\n3. தச்சு வேலை\n4. ஓவியம்\n5. சுத்தம்\n6. சாதன பழுதுபார்ப்பு\n7. HVAC\n8. பூட்டு\n\nதயவுசெய்து ஒரு எண்ணைத் தேர்ந்தெடுக்கவும் அல்லது உங்களுக்கு என்ன தேவை என்று சொல்லுங்கள்."
    },
    'pricing': {
        'en': "Our pricing is transparent and fair:\n\n• Base Service Fee: LKR 500-1000\n• Hourly Rate: LKR 1000-2000/hour\n• Emergency Service: +50% surcharge\n• Materials: Actual cost\n\nFinal cost depends on:\n• Service type\n• Time required\n• Materials needed\n• Distance traveled\n\nYou'll get an estimate before confirming the booking!",
        'si': " අපගේ මිල ගණන් විනිවිද පෙනෙන සහ සාධාරණ වේ:\n\n• මූලික සේවා ගාස්තුව: LKR 500-1000\n• පැය අනුපාතය: LKR 1000-2000/පැය\n• හදිසි සේවාව: +50% අතිරේක ගාස්තුව\n• ද්‍රව්‍ය: සැබෑ පිරිවැය\n\nඅවසාන පිරිවැය රඳා පවතින්නේ:\n✓ සේවා වර්ගය\n✓ අවශ්‍ය කාලය\n✓ අවශ්‍ය ද්‍රව්‍ය\n✓ ගමන් කළ දුර\n\nවෙන්කරවා ගැනීම තහවුරු කිරීමට පෙර ඔබට ඇස්තමේන්තුවක් ලැබෙනු ඇත!",
        'ta': "எங்கள் விலை வெளிப்படையானது மற்றும் நியாயமானது:\n\n• அடிப்படை சேவை கட்டணம்: LKR 500-1000\n• மணிநேர விகிதம்: LKR 1000-2000/மணி\n• அவசர சேவை: +50% கூடுதல் கட்டணம்\n• பொருட்கள்: உண்மையான செலவு\n\nஇறுதி செலவு சார்ந்துள்ளது:\n✓ சேவை வகை\n✓ தேவையான நேரம்\n✓ தேவையான பொருட்கள்\n✓ பயணித்த தூரம்\n\nபதிவை உறுதிப்படுத்துவதற்கு முன் உங்களுக்கு மதிப்பீடு கிடைக்கும்!"
    },
    'status': {
        'en': "To check your booking status, please provide:\n• Your booking ID, or\n• Your registered phone number\n\nYou can also track your technician in real-time from the 'My Bookings' section in the app.",
        'si': "ඔබගේ වෙන්කරවා ගැනීමේ තත්ත්වය පරීක්ෂා කිරීමට, කරුණාකර සපයන්න:",
        'ta': "உங்கள் பதிவு நிலையை சரிபார்க்க, தயவுசெய்து வழங்கவும்:"
    },
    'cancel': {
        'en': "I can help you cancel your booking. Please note:\n\n Cancellation Policy:\n• Free cancellation: Before technician accepts\n• 50% charge: After acceptance, before arrival\n• Full charge: After technician arrives\n\nPlease provide your booking ID to proceed with cancellation.",
        'si': "මට ඔබගේ වෙන්කරවා ගැනීම අවලංගු කිරීමට උදව් කළ හැකිය.",
        'ta': "உங்கள் பதிவை ரத்து செய்ய நான் உதவ முடியும்."
    },
    'complaint': {
        'en': "I'm sorry to hear you're having an issue. \n\nPlease tell me more about the problem:\n• What went wrong?\n• Booking ID (if applicable)\n• What would you like us to do?\n\nYour feedback helps us improve. A support team member will contact you within 24 hours.",
        'si': "ඔබට ගැටලුවක් ඇති බව දැනගැනීමට කණගාටුයි. ",
        'ta': "உங்களுக்கு சிக்கல் இருப்பதைக் கேட்டு வருந்துகிறேன். "
    },
    'payment': {
        'en': "**Payment Information:**\n\nWe accept multiple payment methods:\n• Cash (pay after service)\n• Credit/Debit Cards\n• Mobile Wallets\n• Bank Transfer\n\n**Payment Process:**\n1. Service completed\n2. Technician provides final bill\n3. You review and approve\n4. Choose payment method\n5. Technician confirms receipt\n\nAll payments are secure and tracked in the app!",
        'si': " ගෙවීම් තොරතුරු:",
        'ta': "பணம் செலுத்தும் தகவல்:"
    },
    'rating': {
        'en': "**Rating & Reviews:**\n\nYour feedback helps us improve!\n\nAfter service completion:\n1. Rate your technician (1-5 stars)\n2. Write a review (optional)\n3. Help others make informed decisions\n\nTop-rated technicians get priority matching!\n\nWould you like to rate a recent service?",
        'si': " ශ්‍රේණිගත කිරීම සහ සමාලෝචන:",
        'ta': " மதிப்பீடு மற்றும் விமர்சனங்கள்:"
    },
    'thanks': {
        'en': "You're welcome!  Is there anything else I can help you with?\n\nI can assist with:\n• Booking a service\n• Checking prices\n• Tracking your technician\n• Payment questions\n• General inquiries\n\nFor urgent repairs, just say 'emergency'!",
        'si': "ඔබට සාදරයෙන් පිළිගනිමු! ",
        'ta': "நல்வரவு!"
    },
    'default': {
        'en': "I'm here to help! I can assist you with:\n\n• Booking a service\n• Emergency repairs\n• Pricing information\n• Tracking your technician\n• General questions\n\nWhat would you like to know?",
        'si': "මම උදව් කිරීමට මෙහි සිටිමි! මට ඔබට උදව් කළ හැක්කේ:\n\n• සේවාවක් වෙන්කරවා ගැනීම\n• හදිසි අලුත්වැඩියා\n• මිල ගණන් තොරතුරු\n• ඔබේ කාර්මික ශිල්පියා ලුහුබැඳීම\n• සාමාන්‍ය ප්‍රශ්න\n\nඔබ දැන ගැනීමට කැමති කුමක්ද?",
        'ta': "நான் உதவ இங்கே இருக்கிறேன்! நான் உங்களுக்கு உதவ முடியும்:\n\n• சேவையை பதிவு செய்தல்\n• அவசர பழுதுபார்ப்பு\n• விலை தகவல்\n• உங்கள் தொழில்நுட்ப வல்லுநரைக் கண்காணித்தல்\n• பொது கேள்விகள்\n\nநீங்கள் என்ன தெரிந்து கொள்ள விரும்புகிறீர்கள்?"
    }
}

# Service-Specific Knowledge Base
SERVICE_KNOWLEDGE = {
    'plumbing': {
        'description': "Professional plumbing services for all your water and drainage needs.",
        'common_issues': [
            "Leaking taps/faucets",
            "Clogged drains and toilets",
            "Pipe bursts and leaks",
            "Water heater problems",
            "Low water pressure",
            "Running toilets",
            "Dripping pipes",
            "Sewer line issues"
        ],
        'tips': [
            "Turn off main water valve in case of major leaks",
            "Don't pour grease down drains",
            "Regular maintenance prevents major issues",
            "Use drain strainers to prevent clogs"
        ],
        'emergency_signs': [
            "Water flooding",
            "Burst pipes",
            "No water supply",
            "Sewage backup",
            "Gas leak from water heater"
        ],
        'technician_info': {
            'qualifications': [
                "Licensed and certified plumbers",
                "5+ years of experience",
                "Specialized in residential and commercial plumbing",
                "Trained in modern plumbing techniques"
            ],
            'skills': [
                "Pipe installation and repair",
                "Drain cleaning and unclogging",
                "Water heater installation/repair",
                "Leak detection and fixing",
                "Bathroom and kitchen plumbing",
                "Emergency plumbing services"
            ],
            'tools': [
                "Professional pipe wrenches and cutters",
                "Drain snakes and augers",
                "Leak detection equipment",
                "Pressure testing tools",
                "Modern repair materials"
            ],
            'verification': "All plumbers are background-checked, verified, and insured"
        },
        'avg_time': "1-3 hours",
        'avg_cost': "LKR 2,000 - 8,000"
    },
    'electrical': {
        'description': "Licensed electricians for safe and reliable electrical work.",
        'common_issues': [
            "Power outages",
            "Circuit breaker trips",
            "Faulty outlets/switches",
            "Flickering lights",
            "Electrical shocks",
            "Wiring problems",
            "Panel upgrades",
            "Ceiling fan installation"
        ],
        'tips': [
            "Never touch electrical panels when wet",
            "Turn off breaker before replacing bulbs",
            "Don't overload outlets",
            "Regular electrical inspections recommended"
        ],
        'emergency_signs': [
            "Burning smell from outlets",
            "Sparks or smoke",
            "Frequent breaker trips",
            "Hot outlets or switches",
            "Exposed wires"
        ],
        'technician_info': {
            'qualifications': [
                "Licensed electricians with safety certifications",
                "Trained in electrical codes and standards",
                "7+ years of experience",
                "Specialized in residential and commercial electrical work"
            ],
            'skills': [
                "Wiring and rewiring",
                "Circuit breaker installation",
                "Outlet and switch repair",
                "Lighting installation",
                "Electrical panel upgrades",
                "Safety inspections"
            ],
            'tools': [
                "Multimeters and voltage testers",
                "Wire strippers and crimpers",
                "Circuit tracers",
                "Insulated tools for safety",
                "Professional grade equipment"
            ],
            'verification': "All electricians are licensed, certified, and carry liability insurance"
        },
        'avg_time': "1-4 hours",
        'avg_cost': "LKR 1,500 - 10,000"
    },
    'carpentry': {
        'description': "Skilled carpenters for furniture, doors, and woodwork.",
        'common_issues': [
            "Door repairs and installation",
            "Window frame repairs",
            "Custom furniture",
            "Cabinet installation",
            "Deck building",
            "Wood rot repair",
            "Trim and molding",
            "Shelving installation"
        ],
        'tips': [
            "Use quality wood for durability",
            "Regular polishing maintains finish",
            "Fix squeaky doors with WD-40",
            "Protect wood from moisture"
        ],
        'emergency_signs': [
            "Broken door locks",
            "Damaged door frames",
            "Structural wood damage",
            "Safety hazards from broken furniture"
        ],
        'technician_info': {
            'qualifications': [
                "Skilled carpenters with trade certifications",
                "10+ years of woodworking experience",
                "Expertise in custom furniture and installations",
                "Trained in modern carpentry techniques"
            ],
            'skills': [
                "Custom furniture building",
                "Door and window installation",
                "Cabinet making",
                "Wood repair and restoration",
                "Trim and molding work",
                "Deck and pergola construction"
            ],
            'tools': [
                "Professional power tools",
                "Precision measuring equipment",
                "Wood cutting and shaping tools",
                "Finishing and sanding equipment",
                "Quality hand tools"
            ],
            'verification': "All carpenters are experienced, background-checked, and insured"
        },
        'avg_time': "2-6 hours",
        'avg_cost': "LKR 3,000 - 15,000"
    },
    'painting': {
        'description': "Professional painters for interior and exterior work.",
        'common_issues': [
            "Wall painting",
            "Ceiling painting",
            "Exterior painting",
            "Wood staining",
            "Wallpaper removal",
            "Texture painting",
            "Color consultation",
            "Touch-up work"
        ],
        'tips': [
            "Prep walls before painting",
            "Use primer for better coverage",
            "Choose quality paint for longevity",
            "Protect floors and furniture"
        ],
        'emergency_signs': [
            "Water damage stains",
            "Mold growth on walls",
            "Peeling paint (health hazard)"
        ],
        'technician_info': {
            'qualifications': [
                "Professional painters with 8+ years experience",
                "Trained in color theory and application",
                "Experts in interior and exterior painting",
                "Certified in safe paint handling"
            ],
            'skills': [
                "Wall preparation and priming",
                "Precision painting techniques",
                "Color consultation",
                "Texture and decorative finishes",
                "Wallpaper installation/removal",
                "Exterior painting and weatherproofing"
            ],
            'tools': [
                "Professional spray equipment",
                "Quality brushes and rollers",
                "Surface preparation tools",
                "Scaffolding and ladders",
                "Premium paints and primers"
            ],
            'verification': "All painters are experienced professionals with quality guarantees"
        },
        'avg_time': "4-8 hours per room",
        'avg_cost': "LKR 5,000 - 25,000"
    },
    'cleaning': {
        'description': "Professional cleaning services for homes and offices.",
        'common_issues': [
            "Deep cleaning",
            "Regular maintenance",
            "Move-in/move-out cleaning",
            "Carpet cleaning",
            "Window cleaning",
            "Kitchen deep clean",
            "Bathroom sanitization",
            "Office cleaning"
        ],
        'tips': [
            "Regular cleaning prevents buildup",
            "Use eco-friendly products",
            "Declutter before deep cleaning",
            "Ventilate while cleaning"
        ],
        'emergency_signs': [
            "Pest infestation",
            "Mold growth",
            "Severe odors",
            "Health hazards"
        ],
        'technician_info': {
            'qualifications': [
                "Trained cleaning professionals",
                "5+ years of experience",
                "Certified in sanitation and hygiene",
                "Experts in eco-friendly cleaning"
            ],
            'skills': [
                "Deep cleaning techniques",
                "Carpet and upholstery cleaning",
                "Kitchen and bathroom sanitization",
                "Window and glass cleaning",
                "Floor care and polishing",
                "Odor removal and deodorizing"
            ],
            'tools': [
                "Professional vacuum cleaners",
                "Steam cleaners and sanitizers",
                "Eco-friendly cleaning products",
                "Specialized cleaning equipment",
                "Safety gear and protective equipment"
            ],
            'verification': "All cleaning staff are background-checked, trained, and trustworthy"
        },
        'avg_time': "2-6 hours",
        'avg_cost': "LKR 3,000 - 12,000"
    },
    'appliance_repair': {
        'description': "Expert repair for all home appliances.",
        'common_issues': [
            "Refrigerator not cooling",
            "Washing machine leaks",
            "Dryer not heating",
            "Dishwasher problems",
            "Microwave issues",
            "Oven repairs",
            "AC not cooling",
            "Water dispenser problems"
        ],
        'tips': [
            "Regular maintenance extends life",
            "Clean filters regularly",
            "Don't overload machines",
            "Unplug before cleaning"
        ],
        'emergency_signs': [
            "Electrical sparks",
            "Water leaking heavily",
            "Strange burning smells",
            "Complete failure"
        ],
        'technician_info': {
            'qualifications': [
                "Certified appliance repair technicians",
                "Trained on all major brands",
                "8+ years of experience",
                "Specialized in home appliances"
            ],
            'skills': [
                "Refrigerator repair and maintenance",
                "Washing machine diagnostics",
                "Microwave and oven repair",
                "Dishwasher troubleshooting",
                "AC unit servicing",
                "Electrical component replacement"
            ],
            'tools': [
                "Diagnostic equipment",
                "Specialized repair tools",
                "Genuine replacement parts",
                "Testing instruments",
                "Safety equipment"
            ],
            'verification': "All technicians are certified, experienced, and carry manufacturer warranties"
        },
        'avg_time': "1-3 hours",
        'avg_cost': "LKR 2,000 - 10,000"
    },
    'hvac': {
        'description': "Heating, ventilation, and air conditioning services.",
        'common_issues': [
            "AC not cooling",
            "Poor airflow",
            "Strange noises",
            "High energy bills",
            "Thermostat issues",
            "Refrigerant leaks",
            "Filter replacement",
            "System installation"
        ],
        'tips': [
            "Change filters monthly",
            "Annual maintenance recommended",
            "Keep outdoor unit clear",
            "Set reasonable temperatures"
        ],
        'emergency_signs': [
            "Complete system failure in extreme weather",
            "Refrigerant leaks",
            "Electrical issues",
            "Carbon monoxide detection"
        ],
        'technician_info': {
            'qualifications': [
                "HVAC certified technicians",
                "Licensed refrigeration specialists",
                "10+ years of experience",
                "Trained on modern HVAC systems"
            ],
            'skills': [
                "AC installation and repair",
                "Heating system maintenance",
                "Ventilation optimization",
                "Refrigerant handling",
                "Thermostat installation",
                "Energy efficiency consulting"
            ],
            'tools': [
                "Refrigerant recovery equipment",
                "Pressure gauges and manifolds",
                "Leak detectors",
                "Thermometers and hygrometers",
                "Professional HVAC tools"
            ],
            'verification': "All HVAC technicians are licensed, EPA certified, and insured"
        },
        'avg_time': "1-4 hours",
        'avg_cost': "LKR 3,000 - 15,000"
    },
    'locksmith': {
        'description': "24/7 locksmith services for emergencies and installations.",
        'common_issues': [
            "Locked out",
            "Key replacement",
            "Lock installation",
            "Lock repair",
            "Rekeying",
            "Smart lock installation",
            "Safe opening",
            "Security upgrades"
        ],
        'tips': [
            "Keep spare keys with trusted person",
            "Lubricate locks regularly",
            "Upgrade to deadbolts for security",
            "Change locks when moving"
        ],
        'emergency_signs': [
            "Locked out of home/car",
            "Broken lock",
            "Lost all keys",
            "Security breach"
        ],
        'technician_info': {
            'qualifications': [
                "Licensed locksmiths",
                "Security system certified",
                "15+ years of experience",
                "Experts in all lock types"
            ],
            'skills': [
                "Lock picking and opening",
                "Key cutting and duplication",
                "Lock installation and repair",
                "Smart lock programming",
                "Safe opening and repair",
                "Security system installation"
            ],
            'tools': [
                "Professional lock picks",
                "Key cutting machines",
                "Lock installation tools",
                "Electronic programming devices",
                "Security assessment equipment"
            ],
            'verification': "All locksmiths are licensed, bonded, and background-checked for your security"
        },
        'avg_time': "30 minutes - 2 hours",
        'avg_cost': "LKR 2,000 - 8,000"
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
        'en': "We accept:\nCredit/Debit Cards\n Cash on completion\n Mobile wallets\n Bank transfer\n\nPayment is due after service completion.",
        'si': "අපි පිළිගන්නවා:\n ක්‍රෙඩිට්/ඩෙබිට් කාඩ්පත්",
        'ta': "நாங்கள் ஏற்றுக்கொள்கிறோம்:\n கிரெடிட்/டெபிட் கார்டுகள்"
    },
    'service areas': {
        'en': "We currently serve:\n Colombo and suburbs\n Gampaha\n Kandy\n Galle\n\nExpanding to more areas soon!",
        'si': "අපි දැනට සේවය කරන්නේ:\n කොළඹ සහ තදාසන්න ප්‍රදේශ",
        'ta': "நாங்கள் தற்போது சேவை செய்கிறோம்:\n கொழும்பு மற்றும் புறநகர்"
    },
    'working hours': {
        'en': "Service Hours:\n• Regular: 8 AM - 8 PM\n• Emergency: 24/7 available\n\nEmergency services may have additional charges.",
        'si': " සේවා වේලාවන්:\n• සාමාන්‍ය: පෙ.ව. 8 - ප.ව. 8",
        'ta': " சேவை நேரம்:\n• வழக்கமான: காலை 8 - மாலை 8"
    }
}

def preprocess_text(text):
    """Preprocess text using NLP techniques"""
    if not NLTK_AVAILABLE:
        return text.lower()
    
    try:
        # Tokenize
        tokens = word_tokenize(text.lower())
        
        # Remove stopwords
        stop_words = set(stopwords.words('english'))
        tokens = [word for word in tokens if word.isalnum() and word not in stop_words]
        
        # Lemmatize
        lemmatizer = WordNetLemmatizer()
        tokens = [lemmatizer.lemmatize(word) for word in tokens]
        
        return ' '.join(tokens)
    except:
        return text.lower()

def detect_intent(message):
    """Detect user intent from message with improved accuracy"""
    message_lower = message.lower()
    
    # Score each intent
    intent_scores = {}
    for intent, patterns in INTENT_PATTERNS.items():
        score = 0
        for pattern in patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                score += 1
        intent_scores[intent] = score
    
    # Get intent with highest score
    if max(intent_scores.values()) > 0:
        return max(intent_scores, key=intent_scores.get)
    
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

def get_service_info(service_type, query_lower):
    """Get detailed information about a specific service"""
    if service_type not in SERVICE_KNOWLEDGE:
        return None
    
    service_info = SERVICE_KNOWLEDGE[service_type]
    response = f"**{service_type.replace('_', ' ').title()} Service**\n\n"
    response += f"{service_info['description']}\n\n"
    
    # Check what user is asking about (but NOT if asking for names/list)
    if any(word in query_lower for word in ['qualification', 'certified', 'licensed', 'experienced', 'training']) and not any(word in query_lower for word in ['name', 'names', 'list', 'available', 'show me', 'who are']):
        # Technician information
        tech_info = service_info.get('technician_info', {})
        response += " **Our Technicians:**\n\n"
        
        response += "**Qualifications:**\n"
        for qual in tech_info.get('qualifications', []):
            response += f"✓ {qual}\n"
        
        response += "\n**Skills & Expertise:**\n"
        for skill in tech_info.get('skills', []):
            response += f"• {skill}\n"
        
        response += "\n**Professional Tools:**\n"
        for tool in tech_info.get('tools', []):
            response += f"• {tool}\n"
        
        response += f"\n **{tech_info.get('verification', 'All technicians are verified and insured')}**"
    
    elif any(word in query_lower for word in ['cost', 'price', 'charge', 'fee', 'how much']):
        response += f" **Average Cost:** {service_info['avg_cost']}\n"
        response += f" **Typical Duration:** {service_info['avg_time']}\n\n"
        response += "Note: Final cost depends on the specific issue and materials needed."
    
    elif any(word in query_lower for word in ['problem', 'issue', 'fix', 'repair', 'help']):
        response += "**Common Issues We Fix:**\n"
        for issue in service_info['common_issues'][:5]:
            response += f"• {issue}\n"
        response += f"\n **Typical Duration:** {service_info['avg_time']}"
    
    elif any(word in query_lower for word in ['tip', 'advice', 'prevent', 'maintain', 'care']):
        response += "** Helpful Tips:**\n"
        for tip in service_info['tips']:
            response += f"• {tip}\n"
    
    elif any(word in query_lower for word in ['emergency', 'urgent', 'immediate', 'asap']):
        response += "** Emergency Signs:**\n"
        for sign in service_info['emergency_signs']:
            response += f"• {sign}\n"
        response += "\n If you're experiencing any of these, book an emergency service immediately!"
    
    else:
        # General information
        response += "**Common Issues:**\n"
        for issue in service_info['common_issues'][:4]:
            response += f"• {issue}\n"
        response += f"\n **Cost:** {service_info['avg_cost']}\n"
        response += f"**Duration:** {service_info['avg_time']}\n\n"
        response += "Would you like to book this service?"
    
    return response

def search_faq(query):
    """Search FAQ database"""
    query_lower = query.lower()
    
    for question, answers in FAQ_DATABASE.items():
        if any(word in query_lower for word in question.split()):
            return answers.get('en', '')
    
    return None

def fetch_available_technicians(service_type=None, location=None):
    """Fetch available technicians from backend"""
    try:
        # Build query parameters
        params = {}
        if service_type:
            params['skill'] = service_type  # Backend uses 'skill' not 'skills'
        if location:
            params['location'] = location
        
        # Call backend API
        response = requests.get(
            f'{BACKEND_URL}/api/technicians/available',
            params=params,
            timeout=5
        )
        
        print(f"Backend response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Backend returned: {len(data) if isinstance(data, list) else 'not a list'} technicians")
            # Backend returns array directly, not object with 'technicians' property
            return data if isinstance(data, list) else []
        else:
            print(f"Backend error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching technicians: {e}")
        return None

def format_technician_list(technicians, service_type):
    """Format technician information for display"""
    if not technicians or len(technicians) == 0:
        return f"I don't have specific technician details available right now, but we have qualified {service_type} professionals ready to help you!\n\nWould you like to book a service? Our system will match you with the best available technician in your area."
    
    response = f"**Available {service_type.title()} Technicians:**\n\n"
    
    for i, tech in enumerate(technicians[:5], 1):  # Show max 5 technicians
        # Get user info (backend structure: tech.user.name)
        user = tech.get('user', {})
        name = user.get('name', 'Technician') if isinstance(user, dict) else 'Technician'
        phone = user.get('phone', '') if isinstance(user, dict) else ''
        
        # Get location (backend structure: tech.location.coordinates)
        location = tech.get('location', {})
        # Location is stored as GeoJSON: {type: 'Point', coordinates: [lng, lat]}
        coords = location.get('coordinates', []) if isinstance(location, dict) else []
        
        # Get rating and skills
        rating = tech.get('rating', 0)
        skills = tech.get('skills', [])
        distance = tech.get('distance', None)
        
        response += f"**{i}. {name}**\n"
        
        # Show phone if available
        if phone:
            response += f"   Phone: {phone}\n"
        
        # Show distance if calculated
        if distance and distance < 999:
            response += f"    Distance: {distance:.1f} km away\n"
        
        # Show rating
        response += f"    Rating: {rating:.1f}/5.0\n"
        
        # Show skills
        if skills and len(skills) > 0:
            skills_str = ', '.join(skills[:3])  # Show first 3 skills
            response += f"   Skills: {skills_str}\n"
        
        response += "\n"
    
    response += "Would you like to book one of these technicians? Just say 'book' and I'll help you!"
    return response

def get_conversation_context(user_id):
    """Get conversation context for a user"""
    if user_id not in conversation_contexts:
        conversation_contexts[user_id] = {
            'last_intent': None,
            'last_service': None,
            'booking_in_progress': False,
            'messages': [],
            'created_at': datetime.now().isoformat()
        }
    return conversation_contexts[user_id]

def update_conversation_context(user_id, intent=None, service_type=None, message=None):
    """Update conversation context"""
    context = get_conversation_context(user_id)
    
    if intent:
        context['last_intent'] = intent
    if service_type:
        context['last_service'] = service_type
    if message:
        context['messages'].append({
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        # Keep only last 10 messages
        context['messages'] = context['messages'][-10:]
    
    conversation_contexts[user_id] = context
    return context

def initiate_booking(service_type, user_id):
    """Helper to initiate booking process"""
    context = get_conversation_context(user_id)
    context['booking_in_progress'] = True
    context['booking_service'] = service_type
    
    response = f"**Starting {service_type.replace('_', ' ').title()} Booking**\n\n"
    response += "To complete your booking, I need:\n"
    response += "1. Service type: " + service_type.replace('_', ' ').title() + "\n"
    response += "2. Your location\n"
    response += "3. Urgency level (Regular/Emergency)\n"
    response += "4. Brief description of the issue\n\n"
    response += "Please open the app and tap 'Request Service' to complete your booking, or tell me if this is an emergency!"
    
    return response

def check_payment_status(booking_id):
    """Check payment status for a booking"""
    try:
        response = requests.get(
            f'{BACKEND_URL}/api/bookings/{booking_id}',
            timeout=5
        )
        if response.status_code == 200:
            booking = response.json()
            payment = booking.get('payment', {})
            status = payment.get('status', 'pending')
            method = payment.get('method', 'N/A')
            
            if status == 'completed':
                return f"Payment completed via {method.upper()}"
            elif status == 'pending':
                return f"Payment pending - Method: {method.upper()}"
            else:
                return f"Payment status: {status}"
        return "Unable to fetch payment status"
    except:
        return "Unable to connect to server"

def generate_smart_response(message, service_type, intent, user_id='anonymous'):
    """Generate intelligent contextual responses"""
    message_lower = message.lower()
    
    # Check if asking for technician names/list/details (HIGH PRIORITY)
    asking_for_list = any(phrase in message_lower for phrase in [
        'who are the', 'show me', 'list of', 'available', 
        'names of', 'name of', 'technician names', 'plumber names',
        'electrician names', 'carpenter names', 'painter names',
        'which technicians', 'what technicians'
    ])
    
    asking_for_location = any(word in message_lower for word in ['village', 'location', 'area', 'city', 'where are'])
    
    if (asking_for_list or asking_for_location) and service_type:
        # User is asking for specific technician names/locations
        technicians = fetch_available_technicians(service_type)
        if technicians is not None:
            return format_technician_list(technicians, service_type)
    
    # Check if asking about a specific service
    if service_type:
        service_info = get_service_info(service_type, message_lower)
        if service_info:
            return service_info
    
    # Handle specific question patterns
    question_patterns = {
        'what': ['what is', 'what are', 'what does', 'what can'],
        'how': ['how to', 'how do', 'how can', 'how much'],
        'when': ['when', 'what time'],
        'where': ['where', 'which area'],
        'why': ['why', 'reason'],
        'who': ['who', 'which technician']
    }
    
    # Detect question type
    for q_type, patterns in question_patterns.items():
        if any(pattern in message_lower for pattern in patterns):
            if q_type == 'how' and 'much' in message_lower:
                return "**Pricing Information:**\n\nOur rates vary by service type:\n\n• Plumbing: LKR 2,000 - 8,000\n• Electrical: LKR 1,500 - 10,000\n• Carpentry: LKR 3,000 - 15,000\n• Painting: LKR 5,000 - 25,000\n• Cleaning: LKR 3,000 - 12,000\n• Appliance Repair: LKR 2,000 - 10,000\n• HVAC: LKR 3,000 - 15,000\n• Locksmith: LKR 2,000 - 8,000\n\nFinal cost depends on:\n• Complexity of work\n• Materials required\n• Time needed\n• Emergency surcharge (if applicable)\n\nYou'll get a detailed estimate before confirming!"
            
            elif q_type == 'when':
                return "**Service Hours:**\n\n• **Regular Services:** 8 AM - 8 PM (7 days a week)\n• **Emergency Services:** 24/7 available\n\nNote: Emergency services have a 50% surcharge but we'll be there ASAP!\n\nTypical response times:\n• Regular: Within 2-4 hours\n• Emergency: Within 30-60 minutes"
            
            elif q_type == 'where':
                return "**Service Areas:**\n\nWe currently serve:\n• Colombo and all suburbs\n• Gampaha District\n• Kandy City\n• Galle and surrounding areas\n\nExpanding to more cities soon!\n\nNot sure if we cover your area? Share your location and I'll check for you!"
    
    # Check for specific keywords
    if any(word in message_lower for word in ['leak', 'water', 'pipe', 'tap', 'drain']):
        return get_service_info('plumbing', message_lower)
    
    elif any(word in message_lower for word in ['power', 'electric', 'light', 'switch', 'wiring']):
        return get_service_info('electrical', message_lower)
    
    elif any(word in message_lower for word in ['door', 'window', 'furniture', 'wood', 'cabinet']):
        return get_service_info('carpentry', message_lower)
    
    elif any(word in message_lower for word in ['paint', 'wall', 'color', 'ceiling']):
        return get_service_info('painting', message_lower)
    
    elif any(word in message_lower for word in ['clean', 'maid', 'housekeeping', 'sanitize']):
        return get_service_info('cleaning', message_lower)
    
    elif any(word in message_lower for word in ['fridge', 'washing', 'microwave', 'appliance', 'ac unit']):
        return get_service_info('appliance_repair', message_lower)
    
    elif any(word in message_lower for word in ['ac', 'air conditioning', 'hvac', 'cooling', 'heating']):
        return get_service_info('hvac', message_lower)
    
    elif any(word in message_lower for word in ['lock', 'key', 'locked out', 'security']):
        return get_service_info('locksmith', message_lower)
    
    return None

@app.route('/', methods=['GET'])
def home():
    """Root endpoint"""
    return jsonify({
        'service': 'QuickFix AI Chatbot',
        'version': CHATBOT_CONFIG['version'],
        'status': 'running',
        'endpoints': {
            'health': '/health',
            'chat': '/chat (POST)',
            'intents': '/intents',
            'faq': '/faq',
            'analytics': '/analytics'
        },
        'features': CHATBOT_CONFIG['features'],
        'languages': CHATBOT_CONFIG['languages'],
        'timestamp': datetime.now().isoformat()
    })

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
    """Main chat endpoint with enhanced NLP and context management"""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                'error': 'Message is required'
            }), 400
        
        user_message = data['message']
        # Support both userId and user_id for compatibility
        user_id = data.get('userId') or data.get('user_id', 'anonymous')
        session_id = data.get('sessionId') or data.get('session_id', 'default')
        
        # Debug logging
        print(f"\n=== NEW CHAT REQUEST ===")
        print(f"User ID: {user_id}")
        print(f"Session ID: {session_id}")
        print(f"Message: {user_message}")
        
        # Get conversation context
        context = get_conversation_context(user_id)
        
        # Preprocess message with NLP
        processed_message = preprocess_text(user_message)
        
        # Detect language and intent
        language = detect_language(user_message)
        intent = detect_intent(user_message)
        
        # Extract entities
        service_type = extract_service_type(user_message)
        
        # Check for booking ID in message (for payment/status queries)
        booking_id_match = re.search(r'\b[a-f0-9]{24}\b', user_message)
        booking_id = booking_id_match.group(0) if booking_id_match else None
        
        # Handle payment queries
        if intent == 'payment' and booking_id:
            payment_status = check_payment_status(booking_id)
            bot_response = f"**Payment Status for Booking {booking_id[:8]}...**\n\n{payment_status}\n\nNeed help with anything else?"
        # Handle booking intent with service type
        elif intent == 'booking' and service_type:
            bot_response = initiate_booking(service_type, user_id)
        # Try intelligent response
        else:
            smart_response = generate_smart_response(user_message, service_type, intent, user_id)
            
            # Check FAQ
            faq_response = search_faq(user_message)
            
            # Generate response (priority: smart > faq > intent-based)
            if smart_response:
                bot_response = smart_response
            elif faq_response:
                bot_response = faq_response
            else:
                bot_response = get_response(intent, language)
                
                # Add context-aware suggestions
                if context['last_service'] and intent == 'default':
                    bot_response += f"\n\nI noticed you were asking about {context['last_service']}. Would you like to book this service?"
        
        # Update conversation context
        update_conversation_context(user_id, intent, service_type, user_message)
        
        # Build response
        response_data = {
            'message': bot_response,
            'reply': bot_response,  # For compatibility
            'intent': intent,
            'language': language,
            'timestamp': datetime.now().isoformat(),
            'sessionId': session_id,
            'context': intent
        }
        
        # Add extracted entities
        if service_type:
            response_data['serviceType'] = service_type
            response_data['suggestedAction'] = 'book_service'
        
        if intent == 'emergency':
            response_data['priority'] = 'high'
            response_data['suggestedAction'] = 'emergency_booking'
        
        if intent == 'booking':
            response_data['suggestedAction'] = 'open_booking_screen'
        
        # Add conversation stats
        response_data['conversationStats'] = {
            'messageCount': len(context['messages']),
            'lastIntent': context['last_intent'],
            'lastService': context['last_service']
        }
        
        # Log conversation (in production, save to database)
        print(f"[{datetime.now()}] User {user_id}: {user_message}")
        print(f"[{datetime.now()}] Intent: {intent}, Service: {service_type}")
        print(f"[{datetime.now()}] Bot: {bot_response[:100]}...")
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Internal server error',
            'message': 'Sorry, I encountered an error. Please try again.',
            'reply': 'Sorry, I encountered an error. Please try again.'
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

@app.route('/analytics', methods=['GET'])
def get_analytics():
    """Get chatbot analytics"""
    total_conversations = len(conversation_contexts)
    
    # Calculate intent distribution
    intent_counts = {}
    for context in conversation_contexts.values():
        intent = context.get('last_intent', 'unknown')
        intent_counts[intent] = intent_counts.get(intent, 0) + 1
    
    # Calculate service distribution
    service_counts = {}
    for context in conversation_contexts.values():
        service = context.get('last_service')
        if service:
            service_counts[service] = service_counts.get(service, 0) + 1
    
    return jsonify({
        'totalConversations': total_conversations,
        'intentDistribution': intent_counts,
        'serviceDistribution': service_counts,
        'features': CHATBOT_CONFIG['features'],
        'version': CHATBOT_CONFIG['version'],
        'nltk_enabled': NLTK_AVAILABLE
    })

@app.route('/context/<user_id>', methods=['GET'])
def get_user_context(user_id):
    """Get conversation context for a specific user"""
    context = get_conversation_context(user_id)
    return jsonify(context)

@app.route('/context/<user_id>', methods=['DELETE'])
def clear_user_context(user_id):
    """Clear conversation context for a specific user"""
    if user_id in conversation_contexts:
        del conversation_contexts[user_id]
        return jsonify({'message': 'Context cleared successfully'})
    return jsonify({'message': 'No context found for user'}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f" QuickFix Chatbot v{CHATBOT_CONFIG['version']} starting...")
    print(f" Features: {', '.join(CHATBOT_CONFIG['features'])}")
    print(f" Languages: {', '.join(CHATBOT_CONFIG['languages'])}")
    print(f" NLTK: {'Enabled' if NLTK_AVAILABLE else 'Disabled'}")
    print(f" Backend: {BACKEND_URL}")
    print(f" Server running on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)
