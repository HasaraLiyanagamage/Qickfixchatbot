# QuickFix AI Chatbot Service

Python-based chatbot service with NLP capabilities for 24/7 customer support.

## Features

- ✅ Multi-language support (English, Sinhala, Tamil)
- ✅ Intent recognition (greeting, emergency, booking, pricing, etc.)
- ✅ Entity extraction (service type, urgency)
- ✅ FAQ handling
- ✅ Emergency detection
- ✅ Context-aware responses
- ✅ RESTful API

## Setup

### 1. Install Dependencies

```bash
cd chatbot_service
pip install -r requirements.txt
```

### 2. Run the Service

```bash
python app.py
```

The service will start on `http://localhost:5000`

## API Endpoints

### Health Check
```
GET /health
```

### Chat
```
POST /chat
Content-Type: application/json

{
  "message": "I need a plumber urgently",
  "userId": "user123",
  "sessionId": "session456"
}
```

Response:
```json
{
  "message": "🚨 I understand this is urgent! Let me help you immediately...",
  "intent": "emergency",
  "language": "en",
  "serviceType": "plumbing",
  "priority": "high",
  "suggestedAction": "emergency_booking",
  "timestamp": "2025-01-12T10:30:00",
  "sessionId": "session456"
}
```

### Get Intents
```
GET /intents
```

### Get FAQs
```
GET /faq
```

## Supported Intents

1. **greeting** - Hello, hi, good morning
2. **emergency** - Urgent, ASAP, help
3. **booking** - Book service, need technician
4. **pricing** - Cost, price, how much
5. **status** - Track booking, where is technician
6. **cancel** - Cancel booking
7. **complaint** - Issue, problem, not satisfied
8. **thanks** - Thank you

## Deployment

### Deploy to Render/Heroku

1. Create `Procfile`:
```
web: python app.py
```

2. Deploy:
```bash
git add .
git commit -m "Add chatbot service"
git push heroku main
```

### Environment Variables

- `PORT` - Server port (default: 5000)

## Integration with Backend

Add to your Node.js backend:

```javascript
// routes/chatbot.js
const axios = require('axios');

router.post('/chat', async (req, res) => {
  try {
    const { message, userId } = req.body;
    
    const response = await axios.post('http://localhost:5000/chat', {
      message,
      userId,
      sessionId: req.session.id
    });
    
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: 'Chatbot service unavailable' });
  }
});
```

## Testing

```bash
# Test health
curl http://localhost:5000/health

# Test chat
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I need a plumber", "userId": "test123"}'
```

## Future Enhancements

- [ ] Advanced NLP with spaCy/Rasa
- [ ] Machine learning for intent classification
- [ ] Conversation history storage
- [ ] Sentiment analysis
- [ ] Voice input support
- [ ] Multi-turn conversation context
- [ ] Integration with booking system
- [ ] Analytics dashboard
