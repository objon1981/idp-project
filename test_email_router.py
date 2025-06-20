
#!/usr/bin/env python3
"""
Test script for the email router service
"""
import requests
import json
import time

def test_email_router():
    base_url = "http://0.0.0.0:5001"
    
    print("🧪 Testing Email Router Service")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1. Health Check Test:")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Service Status: {data['status']}")
            print(f"   Routing Rules: {data['routing_rules']}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    # Test 2: Document routing simulation
    print("\n2. Document Routing Test:")
    test_documents = [
        {"filename": "invoice.pdf", "document_type": "pdf"},
        {"filename": "data.json", "document_type": "json"},
        {"filename": "contract.docx", "document_type": "document"},
        {"filename": "receipt.png", "document_type": "image"}
    ]
    
    for doc in test_documents:
        try:
            response = requests.post(f"{base_url}/test", json=doc)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {doc['filename']} → routed to: {data['routed_to']}")
            else:
                print(f"❌ Routing failed for {doc['filename']}")
        except Exception as e:
            print(f"❌ Error testing {doc['filename']}: {e}")
    
    # Test 3: Email processing (demo mode)
    print("\n3. Email Processing Test (Demo Mode):")
    try:
        response = requests.post(f"{base_url}/process")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Process Status: {data['status']}")
            print(f"   Message: {data.get('message', 'N/A')}")
        else:
            print(f"❌ Processing failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Processing error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Email Router Service Testing Complete!")

if __name__ == "__main__":
    test_email_router()
