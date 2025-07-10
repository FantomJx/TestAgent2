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
        # Check for required environment variable
        service_account_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
        if not service_account_json:
            print("Error: Missing required environment variable: FIREBASE_SERVICE_ACCOUNT_JSON")
            return False

        # Parse the JSON string
        service_account_info = json.loads(service_account_json)
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
