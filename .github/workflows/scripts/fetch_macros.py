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
        try:
            service_account_info = json.loads(service_account_json)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in FIREBASE_SERVICE_ACCOUNT_JSON: {e}")
            return False

        # Validate required fields in service account
        required_fields = ['project_id', 'private_key', 'client_email']
        for field in required_fields:
            if field not in service_account_info:
                print(f"Error: Missing required field '{field}' in service account JSON")
                return False

        print(f"Initializing Firebase for project: {service_account_info.get('project_id')}")
        cred = credentials.Certificate(service_account_info)
        firebase_admin.initialize_app(cred)
        print("Firebase initialized successfully")
        return True
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        print(f"Exception type: {type(e).__name__}")
        return False

def fetch_macros():
    """Fetch macro configuration values from Firestore."""
    try:
        print("Getting Firestore client...")
        # Get Firestore client
        db = firestore.client()
        
        print("Fetching macros document from Firestore...")
        # Get reference to macros document with timeout
        doc_ref = db.collection('macros').document('macros')
        
        # Add explicit timeout for the get operation
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Firestore operation timed out")
        
        # Set timeout for 30 seconds
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(30)
        
        try:
            doc = doc_ref.get()
            signal.alarm(0)  # Cancel the alarm
        except TimeoutError:
            print("Error: Firestore operation timed out after 30 seconds")
            return None
        
        if not doc.exists:
            print("Warning: No macros document found in Firestore")
            print("Available collections:")
            try:
                collections = db.collections()
                for collection in collections:
                    print(f"  - {collection.id}")
            except Exception as e:
                print(f"  Could not list collections: {e}")
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
            try:
                with open(github_output_file, 'a') as f:
                    f.write(f"{key.lower()}={value}\n")
            except Exception as e:
                print(f"Warning: Could not write to GitHub output file: {e}")
        
        return macros_data
        
    except Exception as e:
        print(f"Error fetching macros: {e}")
        print(f"Exception type: {type(e).__name__}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
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
