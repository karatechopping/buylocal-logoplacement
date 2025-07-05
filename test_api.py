#!/usr/bin/env python3
"""
Test script for the Logo Placement Analyzer API
"""

import requests
import json
import time

def test_api():
    base_url = "http://localhost:5000"
    
    # Test health check
    print("Testing health check...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Health check status: {response.status_code}")
        print(f"Response: {response.json()}")
    except requests.exceptions.ConnectionError:
        print("❌ API server not running. Please start with: python app.py")
        return
    
    # Test data
    test_data = {
        "image_url": "https://via.placeholder.com/800x600/cccccc/000000?text=Sample+Image",
        "dark_logo_url": "https://via.placeholder.com/100x50/000000/ffffff?text=DARK",
        "light_logo_url": "https://via.placeholder.com/100x50/ffffff/000000?text=LIGHT"
    }
    
    print("\nTesting logo placement analysis...")
    try:
        response = requests.post(
            f"{base_url}/analyze-placement",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200:
            print("✅ API test successful!")
        else:
            print("❌ API test failed")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_api()