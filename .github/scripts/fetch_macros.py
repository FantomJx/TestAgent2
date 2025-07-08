import os
import sys
import json
import firebase_admin
from firebase_admin import credentials, db

# Configuration - Firebase service account file
FIREBASE_SERVICE_ACCOUNT_FILE = "pr-agent-21ba8-firebase-adminsdk-fbsvc-95c716d6e2.json"

def initialize_firebase():
    """Initialize Firebase Admin SDK using service account JSON file."""
    try:
        # Get the path to the service account file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        github_dir = os.path.dirname(script_dir)
        service_account_path = os.path.join(github_dir, FIREBASE_SERVICE_ACCOUNT_FILE)
        
        if not os.path.exists(service_account_path):
            raise FileNotFoundError(f"Firebase service account file not found at: {service_account_path}")
        
        # Load the service account JSON
        with open(service_account_path, 'r') as f:
            service_account_info = json.load(f)
        
        # Initialize Firebase Admin with the service account file
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)
        
        print("✅ Firebase initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error initializing Firebase: {e}")
        return False

def fetch_macros():
    """Fetch macro configuration values from Firebase."""
    try:
        # Get reference to macros node
        ref = db.reference('macros')
        macros_data = ref.get()
        
        if not macros_data:
            print("⚠️  No macros data found in Firebase")
            return None
        
        print("✅ Successfully fetched macros from Firebase:")
        
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
            print(f"  {key}={value}")
            
            # Set GitHub Actions output
            with open(os.environ.get('GITHUB_OUTPUT', '/dev/stdout'), 'a') as f:
                f.write(f"{key.lower()}={value}\n")
        
        return macros_data
        
    except Exception as e:
        print(f"❌ Error fetching macros: {e}")
        return None

def main():
    """Main function."""
    print("🔥 Fetching macro configuration from Firebase...")
    
    # Initialize Firebase
    if not initialize_firebase():
        sys.exit(1)
    
    # Fetch macros
    macros = fetch_macros()
    if macros is None:
        print("❌ Failed to fetch macros")
        sys.exit(1)
    
    print("✅ Macro fetch completed successfully")

if __name__ == "__main__":
    main()
