import os
import json
import base64
from firebase_client import FirebaseClient

def main():
    try:
        firebase_client = FirebaseClient()
        repository = os.environ['REPOSITORY']
        
        # Get current architecture summary
        architecture_summary = firebase_client.get_architecture_summary(repository)
        
        # Get recent changes for additional context
        recent_changes = firebase_client.get_recent_changes(repository, limit=5)
        
        # Prepare context data
        context_data = {
            'architecture_summary': architecture_summary,
            'recent_changes': recent_changes,
            'repository': repository
        }
        
        # Encode context as base64
        context_json = json.dumps(context_data, default=str)
        context_b64 = base64.b64encode(context_json.encode('utf-8')).decode('utf-8')
        
        print(f"context_b64={context_b64}")
        
    except Exception as e:
        print(f"Error fetching Firebase context: {e}")
        # Provide empty context on error
        empty_context = base64.b64encode(json.dumps({}).encode('utf-8')).decode('utf-8')
        print(f"context_b64={empty_context}")
        exit(1)

if __name__ == "__main__":
    main()
