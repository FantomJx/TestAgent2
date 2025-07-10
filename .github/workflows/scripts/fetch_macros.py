#!/usr/bin/env python3
import os
import sys
import json

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except ImportError as e:
    print(f"Failed to import firebase_admin: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Unexpected error importing firebase_admin: {e}")
    sys.exit(1)

def initialize_firebase():
    """Initialize Firebase Admin SDK using service account JSON file."""
    try:
        # Required environment variables
        required_env_vars = [
            "FIREBASE_PROJECT_ID",
            "FIREBASE_PRIVATE_KEY",
            "FIREBASE_CLIENT_EMAIL"
        ]
        missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
        if missing_vars:
            print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
            return False

        # Build service account info from environment variables (GitHub secrets)
        service_account_info = {
                    "type": "service_account",
                    "project_id": os.environ.get("FIREBASE_PROJECT_ID"),
                    "private_key_id": "92386836308c1cb6294effbea156da5ff8e63434",
                    "private_key": os.environ.get("FIREBASE_PRIVATE_KEY").replace('\\n', ''),
                    "client_email": os.environ.get("FIREBASE_CLIENT_EMAIL"),
                    "client_id": "109866713813341583021",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40pr-agent-21ba8.iam.gserviceaccount.com"
                }
        cred = credentials.Certificate(service_account_info)
        firebase_admin.initialize_app(cred)
        print("Firebase initialized successfully")
        return True
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        return False

def fetch_macros():
    """Fetch macro configuration values from Firestore."""
    try:
        # Get Firestore client
        db = firestore.client()
        
        # Get reference to macros document
        doc_ref = db.collection('macros').document('macros')
        doc = doc_ref.get()
        
        if not doc.exists:
            print("No macros document found in Firestore")
            return None
        
        macros_data = doc.to_dict()
        print("Successfully fetched macros from Firestore:")
        
        # Define expected macro keys with defaults
        expected_macros = {
            'LINE_THRESHOLD': '200',
            'CHANGES_THRESHOLD': '5',
            'IMPORTANT_CHANGE_MARKERS': '#IMPORTANT-CHANGE,#IMPORTANT-CHANGES',
            'IMPORTANT_CHANGE_LABELS': 'important change,important changes'
        }
        
        # Extract values and set GitHub outputs
        for key, default_value in expected_macros.items():
            value = macros_data.get(key, default_value)
            print(f"  Key: '{key}' |  Value: {value}")
            
            # Set GitHub Actions output
            github_output_file = os.environ.get('GITHUB_OUTPUT', '/dev/stdout')
            with open(github_output_file, 'a') as f:
                f.write(f"{key.lower()}={value}\n")
        
        return macros_data
        
    except Exception as e:
        print(f"Error fetching macros: {e}")
        return None

def main():
    print("Fetching macro configuration from Firebase...")
    
    # Initialize Firebase
    if not initialize_firebase():
        sys.exit(1)
    
    # Fetch macros
    macros = fetch_macros()
    if macros is None:
        print("Failed to fetch macros")
        sys.exit(1)
    
    print("Macro fetch completed successfully")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Exception in main: {e}")
        sys.exit(1)
