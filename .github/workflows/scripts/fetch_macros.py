#!/usr/bin/env python3
import os
import sys
import json

print(f"DEBUG: fetch_macros.py loaded, __name__={__name__}")
print(f"DEBUG: Current working directory: {os.getcwd()}")
print(f"DEBUG: Script path: {__file__}")
print(f"DEBUG: Python path: {sys.path}")
print(f"DEBUG: Environment variables present: {list(os.environ.keys())}")

try:
    print("DEBUG: Attempting to import firebase_admin")
    import firebase_admin
    from firebase_admin import credentials, firestore
    print("DEBUG: firebase_admin imported successfully")
except ImportError as e:
    print(f"DEBUG: Failed to import firebase_admin: {e}")
    print("DEBUG: This might indicate firebase-admin is not installed")
    sys.exit(1)
except Exception as e:
    print(f"DEBUG: Unexpected error importing firebase_admin: {e}")
    sys.exit(1)

def initialize_firebase():
    """Initialize Firebase Admin SDK using service account JSON file."""
    print("DEBUG: initialize_firebase() called")
    try:
        # Required environment variables
        required_env_vars = [
            "FIREBASE_PROJECT_ID",
            "FIREBASE_PRIVATE_KEY",
            "FIREBASE_CLIENT_EMAIL"
        ]
        print(f"DEBUG: Checking for required environment variables: {required_env_vars}")
        missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
        if missing_vars:
            print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
            print(f"DEBUG: Available environment variables: {[var for var in required_env_vars if os.environ.get(var)]}")
            return False

        print("DEBUG: All required environment variables found")
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
        print("DEBUG: Service account info created")
        cred = credentials.Certificate(service_account_info)
        print("DEBUG: Firebase credentials object created")
        firebase_admin.initialize_app(cred)
        print("Firebase initialized successfully")
        return True
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        print(f"DEBUG: Exception type: {type(e)}")
        import traceback
        traceback.print_exc()
        return False

def fetch_macros():
    """Fetch macro configuration values from Firestore."""
    print("DEBUG: fetch_macros() called")
    try:
        # Get Firestore client
        print("DEBUG: Getting Firestore client")
        db = firestore.client()
        
        # Get reference to macros document
        print("DEBUG: Getting macros document reference")
        doc_ref = db.collection('macros').document('macros')
        print("DEBUG: Fetching document")
        doc = doc_ref.get()
        
        if not doc.exists:
            print("No macros document found in Firestore")
            print("DEBUG: Document does not exist")
            return None
        
        print("DEBUG: Document exists, converting to dict")
        macros_data = doc.to_dict()
        print("Successfully fetched macros from Firestore:")
        print(f"DEBUG: Raw macros data: {macros_data}")
        
        # Define expected macro keys with defaults
        expected_macros = {
            'LINE_THRESHOLD': '200',
            'CHANGES_THRESHOLD': '5',
            'IMPORTANT_CHANGE_MARKERS': '#IMPORTANT-CHANGE,#IMPORTANT-CHANGES',
            'IMPORTANT_CHANGE_LABELS': 'important change,important changes'
        }
        
        print("DEBUG: Processing macros and setting GitHub outputs")
        # Extract values and set GitHub outputs
        for key, default_value in expected_macros.items():
            value = macros_data.get(key, default_value)
            print(f"  Key: '{key}' |  Value: {value}")
            
            # Set GitHub Actions output
            github_output_file = os.environ.get('GITHUB_OUTPUT', '/dev/stdout')
            print(f"DEBUG: Writing to GitHub output file: {github_output_file}")
            with open(github_output_file, 'a') as f:
                f.write(f"{key.lower()}={value}\n")
        
        print("DEBUG: fetch_macros() completed successfully")
        return macros_data
        
    except Exception as e:
        print(f"Error fetching macros: {e}")
        print(f"DEBUG: Exception type: {type(e)}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("DEBUG: main() function called")
    print("Fetching macro configuration from Firebase...")
    
    # Initialize Firebase
    if not initialize_firebase():
        print("DEBUG: Firebase initialization failed")
        sys.exit(1)
    
    # Fetch macros
    macros = fetch_macros()
    if macros is None:
        print("Failed to fetch macros")
        print("DEBUG: fetch_macros returned None")
        sys.exit(1)
    
    print("Macro fetch completed successfully")
    print("DEBUG: main() function completed successfully")

if __name__ == "__main__":
    print("DEBUG: __main__ branch starting main()")
    try:
        main()
    except Exception as e:
        print(f"DEBUG: Exception in main: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
