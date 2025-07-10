import os
import sys
import json
import firebase_admin
from firebase_admin import credentials, firestore
import time  # Added for timing measurements

# Configuration - Firebase service account file
FIREBASE_SERVICE_ACCOUNT_FILE = "pr-agent-21ba8-firebase-adminsdk-fbsvc-95c716d6e2.json"

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
                    "private_key": os.environ.get("FIREBASE_PRIVATE_KEY").replace('\\n', '\n'),
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
        # Get Firestore client with timing
        print("Connecting to Firestore...")
        start_time = time.time()
        db = firestore.client()
        print(f"Connected to Firestore in {time.time() - start_time:.2f}s")
        
        # Get reference to macros document and fetch with timing and timeout
        doc_ref = db.collection('macros').document('macros')
        print("Retrieving macros document...")
        start_time = time.time()
        doc = doc_ref.get(timeout=10)
        elapsed = time.time() - start_time
        print(f"Document fetch elapsed time: {elapsed:.2f}s")
        
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
            with open(os.environ.get('GITHUB_OUTPUT', '/dev/stdout'), 'a') as f:
                f.write(f"{key.lower()}={value}\n")
        
        return macros_data
        
    except Exception as e:
        print(f"Error fetching macros: {e}")
        return None

def main():
    """Main function."""
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
    main()
