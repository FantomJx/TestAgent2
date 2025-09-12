import os
import base64
import sys
from firebase_client import FirebaseClient
from local_architecture import LocalArchitectureManager
from config import PROJECT_NAME

def main():
    try:
        # Initialize both local and Firebase clients
        project_name = PROJECT_NAME
        firebase_client = FirebaseClient(project_name=project_name)
        local_manager = LocalArchitectureManager()
        
        # Get required environment variables
        repository = os.environ['REPOSITORY']
        pr_number = int(os.environ['PR_NUMBER'])
        diff_file_path = os.environ['DIFF_FILE_PATH']
        is_summary_only = os.environ.get('IS_SUMMARY_ONLY', 'false').lower() == 'true'
    
        print(f"Tracking architecture for project: {project_name}, repository: {repository}", file=sys.stderr)
        
        # Read the diff from file
        with open(diff_file_path, 'r', encoding='utf-8') as f:
            diff = f.read()
        
        # Get additional metadata
        metadata = {
            'head_sha': os.environ.get('HEAD_SHA'),
            'base_sha': os.environ.get('BASE_SHA'),
            'pr_title': os.environ.get('PR_TITLE'),
            'pr_author': os.environ.get('PR_AUTHOR'),
            'pr_description': os.environ.get('PR_DESCRIPTION', '')
        }
        
        # Add the architecture change to both local and Firebase
        local_change_id = local_manager.add_architecture_change(
            pr_number=pr_number,
            diff=diff,
            metadata=metadata
        )
        print(f"Local architecture change added with ID: {local_change_id}", file=sys.stderr)
        
        # Also add to Firebase for backup/sync
        try:
            firebase_change_id = firebase_client.add_architecture_change(
                repository=repository,
                pr_number=pr_number,
                diff=diff,
                metadata=metadata
            )
            print(f"Firebase architecture change added with ID: {firebase_change_id}", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Firebase tracking failed, continuing with local only: {e}", file=sys.stderr)
        
        # Check if we should regenerate the summary (prefer local logic, fallback to Firebase)
        diff_size = len(diff)
        pr_description = metadata.get('pr_description', '')
        
        should_summarize_local = local_manager.should_summarize(diff_size=diff_size, pr_description=pr_description)
        print(f"Local should_summarize: {should_summarize_local}", file=sys.stderr)
        
        # Also check Firebase logic for comparison
        try:
            should_summarize_firebase = firebase_client.should_summarize(repository, diff_size=diff_size, pr_description=pr_description)
            print(f"Firebase should_summarize: {should_summarize_firebase}", file=sys.stderr)
            
            # Use OR logic - summarize if either thinks we should
            should_summarize = should_summarize_local or should_summarize_firebase
        except Exception as e:
            print(f"Warning: Firebase should_summarize failed, using local only: {e}", file=sys.stderr)
            should_summarize = should_summarize_local
        
        print(f"Final should_summarize decision: {should_summarize}", file=sys.stderr)
        
        # Write outputs to GitHub Actions output file (strip any carriage returns)
        if 'GITHUB_OUTPUT' in os.environ:
            clean_should_summarize = str(should_summarize).lower().replace('\r', '').replace('\n', ' ')
            clean_change_id = str(local_change_id or 'none').replace('\r', '').replace('\n', ' ')
            with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
                fh.write(f"should_summarize={clean_should_summarize}\n")
                fh.write(f"change_id={clean_change_id}\n")
        else:
            # Fallback for local testing
            print(f"should_summarize={str(should_summarize).lower()}", file=sys.stderr)
            print(f"change_id={local_change_id or 'none'}", file=sys.stderr)
        
    except Exception as e:
        print(f"Error tracking architecture: {e}", file=sys.stderr)
        
        # Write error output to GitHub Actions output file
        if 'GITHUB_OUTPUT' in os.environ:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
                fh.write("should_summarize=false\n")
        else:
            # Fallback for local testing
            print("should_summarize=false", file=sys.stderr)
        exit(1)

if __name__ == "__main__":
    main()