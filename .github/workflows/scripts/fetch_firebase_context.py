import os
import json
import base64
import time
import sys
from datetime import datetime
from firebase_client import FirebaseClient
from config import PROJECT_NAME

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
    empty_context = {
        'architecture_summary': None,
        'recent_changes': [],
        'repository': os.environ.get('REPOSITORY', 'unknown'),
        'project_name': PROJECT_NAME,
        'status': 'fallback'
    }
    context_json = json.dumps(empty_context)
    return base64.b64encode(context_json.encode('utf-8')).decode('utf-8')



def main():
    repository = os.environ.get('REPOSITORY')
    
    if not repository:
        print("Error: REPOSITORY environment variable not set", file=sys.stderr)
        print(f"context_b64={create_empty_context()}", file=sys.stderr)
        return
    
    try:
        def fetch_firebase_data():
            firebase_client = FirebaseClient()
            
            # Get current architecture summary
            architecture_summary = firebase_client.get_architecture_summary(repository)
            
            # If no architecture summary found in Firebase, that's normal for new repositories
            if not architecture_summary:
                print(f"No architecture summary found for {repository} in project {PROJECT_NAME} (this is normal for new repositories)", file=sys.stderr)
            
            # Get recent changes for additional context
            # recent_changes = firebase_client.get_recent_changes(repository, limit=5)
            
            return {
                'architecture_summary': architecture_summary,
                # 'recent_changes': recent_changes,
                'repository': repository,
                'project_name': PROJECT_NAME,
                'status': 'success'
            }
        
        # Try to fetch data with retries
        context_data = retry_with_backoff(fetch_firebase_data)
        
        # Encode context as base64
        context_json = json.dumps(context_data, default=str)
        context_b64 = base64.b64encode(context_json.encode('utf-8')).decode('utf-8')
        
        # Write output to GitHub Actions output file (strip any carriage returns)
        if 'GITHUB_OUTPUT' in os.environ:
            clean_context_b64 = str(context_b64).replace('\r', '').replace('\n', '')
            with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
                fh.write(f"context_b64={clean_context_b64}\n")
        else:
            # Fallback for local testing
            print(f"context_b64={context_b64}", file=sys.stderr)
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error fetching Firebase context: {error_msg}", file=sys.stderr)
        
        # Provide empty context on error but don't exit with error code
        # This allows the workflow to continue even if Firebase is unavailable
        empty_context_b64 = create_empty_context()
        
        # Write output to GitHub Actions output file (strip any carriage returns)
        if 'GITHUB_OUTPUT' in os.environ:
            clean_empty_context_b64 = str(empty_context_b64).replace('\r', '').replace('\n', '')
            with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
                fh.write(f"context_b64={clean_empty_context_b64}\n")
        else:
            # Fallback for local testing
            print(f"context_b64={empty_context_b64}", file=sys.stderr)
        
        # Only exit with error code for critical failures
        if 'REPOSITORY' not in os.environ:
            sys.exit(1)

if __name__ == "__main__":
    main()
