# QuickFix Chatbot v2.0 - Deployment Guide

## 🚀 Quick Start

### Local Development

```bash
# Navigate to chatbot directory
cd chatbot

# Install dependencies
pip install -r requirements.txt

# Run the chatbot
python app.py
```

The chatbot will start on `http://localhost:5000`

---

## 📦 Dependencies

The chatbot will automatically download required NLTK data on first run:
- punkt (tokenizer)
- stopwords
- wordnet (lemmatizer)

If you encounter issues, manually download:

```python
import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
```

---

## 🌐 Production Deployment

### Option 1: Render (Recommended)

1. **Push to Git**
```bash
git add .
git commit -m "Enhanced chatbot v2.0"
git push
```

2. **Render will automatically:**
   - Detect `requirements.txt`
   - Install all dependencies (including NLTK)
   - Download NLTK data on first run
   - Start the service

3. **Environment Variables**
Set in Render dashboard:
```
BACKEND_URL=https://quickfix-backend-6ztz.onrender.com
PORT=5000
```

### Option 2: Heroku

1. **Ensure Procfile exists:**
```
web: gunicorn app:app
```

2. **Deploy:**
```bash
git push heroku main
```

3. **Set environment variables:**
```bash
heroku config:set BACKEND_URL=https://quickfix-backend-6ztz.onrender.com
```

---

## 🧪 Testing

### Test Health Endpoint
```bash
curl http://localhost:5000/health
```

### Test Chat
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "userId": "test123"}'
```

### Test Analytics
```bash
curl http://localhost:5000/analytics
```

---

## ✅ Verification Checklist

- [ ] All dependencies installed
- [ ] NLTK data downloaded
- [ ] Health endpoint responds
- [ ] Chat endpoint works
- [ ] Analytics endpoint works
- [ ] Backend connection successful
- [ ] Logs show correct version (2.0.0)
- [ ] NLP features enabled

---

## 🔧 Troubleshooting

### NLTK Data Not Found
```python
import nltk
nltk.download('all')  # Download all NLTK data
```

### Backend Connection Failed
Check `BACKEND_URL` environment variable is set correctly.

### Import Errors
```bash
pip install --upgrade -r requirements.txt
```

---

## 📊 Monitoring

Check logs for:
```
🤖 QuickFix Chatbot v2.0.0 starting...
📦 Features: NLP, Multi-language, Context-aware, Booking Integration
🧠 NLTK: Enabled
```

If you see "NLTK: Disabled", the NLP features will fall back to basic processing.

---

## 🎉 Success!

Your enhanced chatbot is now running with:
- ✅ Advanced NLP
- ✅ Context management
- ✅ Payment integration
- ✅ Analytics
- ✅ 10 intents
- ✅ 3 languages
