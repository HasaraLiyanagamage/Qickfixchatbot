#!/usr/bin/env python3
"""
Quick test script for QuickFix Chatbot
Run this locally to verify everything works before deploying
"""

import requests
import json

# Test locally or change to your deployed URL
BASE_URL = "http://localhost:5000"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed!")
            print(f"   Version: {data.get('version')}")
            print(f"   Status: {data.get('status')}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_chat(message):
    """Test chat endpoint"""
    print(f"\n💬 Testing chat: '{message}'")
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"message": message, "userId": "test_user"},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Chat response received!")
            print(f"   Intent: {data.get('intent')}")
            print(f"   Service: {data.get('serviceType', 'N/A')}")
            print(f"   Reply: {data.get('reply', data.get('message'))[:100]}...")
            return True
        else:
            print(f"❌ Chat failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_analytics():
    """Test analytics endpoint"""
    print("\n📊 Testing analytics endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/analytics")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Analytics retrieved!")
            print(f"   Total Conversations: {data.get('totalConversations')}")
            print(f"   NLTK Enabled: {data.get('nltk_enabled')}")
            print(f"   Features: {', '.join(data.get('features', []))}")
            return True
        else:
            print(f"❌ Analytics failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("🤖 QuickFix Chatbot Test Suite\n")
    print("=" * 50)
    
    # Test health
    if not test_health():
        print("\n⚠️  Chatbot is not running. Start it with: python app.py")
        return
    
    # Test various chat scenarios
    test_messages = [
        "Hello",
        "I need a plumber",
        "How much does it cost?",
        "Emergency! Water leak!",
        "How can I pay?",
        "I want to book electrical service"
    ]
    
    for msg in test_messages:
        test_chat(msg)
    
    # Test analytics
    test_analytics()
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")

if __name__ == "__main__":
    main()
