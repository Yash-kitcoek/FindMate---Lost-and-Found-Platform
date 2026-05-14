"""
Test Script for FindMate ML Service
Run this to verify the service is working correctly
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
BASE_URL = os.getenv('ML_SERVICE_URL', 'http://localhost:5000')
API_KEY = os.getenv('ML_SERVICE_API_KEY', 'your-api-key')

def test_health_check():
    """Test health check endpoint"""
    print("\n=== Testing Health Check ===")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_match_lost_to_found():
    """Test matching a lost item"""
    print("\n=== Testing Lost to Found Matching ===")
    
    headers = {
        'X-API-Key': API_KEY,
        'Content-Type': 'application/json'
    }
    
    data = {
        'itemId': 'test-lost-001',
        'itemName': 'Blue iPhone 13',
        'category': 'electronics',
        'description': 'Blue iPhone 13 with black protective case, small scratch on back',
        'location': 'Library',
        'date': '2024-02-15',
        'color': 'blue',
        'brand': 'Apple'
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/match/lost-to-found",
            headers=headers,
            json=data
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_match_found_to_lost():
    """Test matching a found item"""
    print("\n=== Testing Found to Lost Matching ===")
    
    headers = {
        'X-API-Key': API_KEY,
        'Content-Type': 'application/json'
    }
    
    data = {
        'itemId': 'test-found-001',
        'itemName': 'Black backpack',
        'category': 'bags',
        'description': 'Nike black backpack with laptop compartment and water bottle holder',
        'location': 'Ground',
        'date': '2024-02-16',
        'brand': 'Nike'
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/match/found-to-lost",
            headers=headers,
            json=data
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_invalid_api_key():
    """Test with invalid API key"""
    print("\n=== Testing Invalid API Key ===")
    
    headers = {
        'X-API-Key': 'invalid-key',
        'Content-Type': 'application/json'
    }
    
    data = {
        'itemId': 'test-001',
        'itemName': 'Test Item',
        'category': 'other',
        'description': 'Test description',
        'location': 'Test location',
        'date': '2024-02-15'
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/match/lost-to-found",
            headers=headers,
            json=data
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 403  # Should be forbidden
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_missing_fields():
    """Test with missing required fields"""
    print("\n=== Testing Missing Required Fields ===")
    
    headers = {
        'X-API-Key': API_KEY,
        'Content-Type': 'application/json'
    }
    
    # Missing 'description' field
    data = {
        'itemId': 'test-001',
        'itemName': 'Test Item',
        'category': 'other',
        'location': 'Test location',
        'date': '2024-02-15'
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/match/lost-to-found",
            headers=headers,
            json=data
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 400  # Should be bad request
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def run_all_tests():
    """Run all tests and report results"""
    print("=" * 60)
    print("FindMate ML Service - Test Suite")
    print("=" * 60)
    print(f"Testing service at: {BASE_URL}")
    print(f"Using API Key: {API_KEY[:10]}...")
    
    tests = [
        ("Health Check", test_health_check),
        ("Match Lost to Found", test_match_lost_to_found),
        ("Match Found to Lost", test_match_found_to_lost),
        ("Invalid API Key", test_invalid_api_key),
        ("Missing Required Fields", test_missing_fields)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {str(e)}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Service is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")

if __name__ == '__main__':
    run_all_tests()
