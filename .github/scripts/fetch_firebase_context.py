import os
import json
import base64
import time
import sys
from firebase_client import FirebaseClient

def retry_with_backoff(func, max_retries=3, base_delay=1):
    """Retry function with exponential backoff"""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            
            # Check for specific errors that shouldn't be retried
            error_str = str(e).lower()
            if any(term in error_str for term in ['invalid_grant', 'account not found', 'authentication']):
                raise e
            
            delay = base_delay * (2 ** attempt)
            print(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay} seconds...", file=sys.stderr)
            time.sleep(delay)

def create_empty_context():
    """Create empty context for fallback"""
    project_name = "PR-AGENT"  # Hardcoded project name
    empty_context = {
        'architecture_summary': None,
        'recent_changes': [],
        'repository': os.environ.get('REPOSITORY', 'unknown'),
        'project_name': project_name,
        'status': 'fallback'
    }
    context_json = json.dumps(empty_context)
    return base64.b64encode(context_json.encode('utf-8')).decode('utf-8')

def main():
    repository = os.environ.get('REPOSITORY')
    project_name = "PR-AGENT"  # Hardcoded project name
    
    if not repository:
        print("Error: REPOSITORY environment variable not set", file=sys.stderr)
        print(f"context_b64={create_empty_context()}")
        return
    
    try:
        def fetch_firebase_data():
            firebase_client = FirebaseClient()
            
            # Get current architecture summary
            architecture_summary = firebase_client.get_architecture_summary(repository)
            
            # Get recent changes for additional context
            recent_changes = firebase_client.get_recent_changes(repository, limit=5)
            
            return {
                'architecture_summary': architecture_summary,
                'recent_changes': recent_changes,
                'repository': repository,
                'project_name': project_name,
                'status': 'success'
            }
        
        # Try to fetch data with retries
        context_data = retry_with_backoff(fetch_firebase_data)
        
        # Encode context as base64
        context_json = json.dumps(context_data, default=str)
        context_b64 = base64.b64encode(context_json.encode('utf-8')).decode('utf-8')
        
        print(f"context_b64={context_b64}")
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error fetching Firebase context: {error_msg}", file=sys.stderr)
        
        # Provide empty context on error but don't exit with error code
        # This allows the workflow to continue even if Firebase is unavailable
        empty_context_b64 = create_empty_context()
        print(f"context_b64={empty_context_b64}")
        
        # Only exit with error code for critical failures
        if 'REPOSITORY' not in os.environ:
            sys.exit(1)

if __name__ == "__main__":
    main()
