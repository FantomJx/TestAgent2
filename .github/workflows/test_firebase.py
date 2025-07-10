#!/usr/bin/env python3
"""
Simple Firebase connectivity test script
"""
import os
import sys
import json
import time

def test_firebase_connectivity():
    """Test Firebase connectivity with detailed error reporting"""
    try:
        print("=== Firebase Connectivity Test ===")
        
        # Check environment variable
        service_account_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
        if not service_account_json:
            print("❌ FIREBASE_SERVICE_ACCOUNT_JSON environment variable is missing")
            return False
        
        print("✅ FIREBASE_SERVICE_ACCOUNT_JSON environment variable is present")
        
        # Test JSON parsing
        try:
            service_account_info = json.loads(service_account_json)
            print("✅ Service account JSON is valid")
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in service account: {e}")
            return False
        
        # Check required fields
        required_fields = ['project_id', 'private_key', 'client_email']
        for field in required_fields:
            if field not in service_account_info:
                print(f"❌ Missing required field '{field}' in service account")
                return False
        
        print("✅ All required fields present in service account")
        project_id = service_account_info.get('project_id')
        print(f"📋 Project ID: {project_id}")
        
        # Test Firebase imports
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore
            print("✅ Firebase admin imports successful")
        except ImportError as e:
            print(f"❌ Firebase admin import failed: {e}")
            return False
        
        # Test Firebase initialization
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(service_account_info)
                firebase_admin.initialize_app(cred)
                print("✅ Firebase app initialized successfully")
            else:
                print("✅ Firebase app already initialized")
        except Exception as e:
            print(f"❌ Firebase initialization failed: {e}")
            return False
        
        # Test Firestore client
        try:
            db = firestore.client()
            print("✅ Firestore client created successfully")
        except Exception as e:
            print(f"❌ Firestore client creation failed: {e}")
            return False
        
        # Test simple read operation with timeout
        try:
            print("🔍 Testing Firestore read operation...")
            start_time = time.time()
            
            # Try to read a test document
            doc_ref = db.collection('test').document('connectivity')
            doc = doc_ref.get(timeout=30)  # 30 second timeout
            
            elapsed = time.time() - start_time
            print(f"✅ Firestore read operation completed in {elapsed:.2f} seconds")
            
            if doc.exists:
                print("📄 Test document exists in Firestore")
            else:
                print("📄 Test document does not exist (this is normal)")
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ Firestore read operation failed after {elapsed:.2f} seconds: {e}")
            return False
        
        print("✅ All Firebase connectivity tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Unexpected error during Firebase test: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_firebase_connectivity()
    sys.exit(0 if success else 1)
