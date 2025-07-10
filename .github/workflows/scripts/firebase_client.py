import os
import json
import sys
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import base64
import logging
from fetch_macros import initialize_firebase, fetch_macros

# Configuration - Firebase service account file
FIREBASE_SERVICE_ACCOUNT_FILE = "pr-agent.json"

class FirebaseClient:
    def __init__(self, service_account_path=None, project_name="test"):
        try:
            if not firebase_admin._apps:
                # Use provided path or default to the JSON file
                if not service_account_path:
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    workflows_dir = os.path.dirname(script_dir)
                    github_dir = os.path.dirname(workflows_dir)
                    service_account_path = os.path.join(github_dir, FIREBASE_SERVICE_ACCOUNT_FILE)
                
                if not os.path.exists(service_account_path):
                    raise FileNotFoundError(f"Firebase credentials file not found at: {service_account_path}")
                    
                cred = credentials.Certificate(service_account_path)
                firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
            self.project_name = project_name
        except Exception as e:
            logging.error(f"Failed to initialize Firebase: {str(e)}")
            raise
    
    def get_architecture_summary(self, repository):
        """Get the current architecture summary for a repository"""
        if not repository:
            return None
            
        try:
            # Use project_name as the main collection path
            doc_ref = self.db.collection(self.project_name).document('architecture_summaries').collection('summaries').document(repository.replace('/', '_'))
            doc = doc_ref.get()
            if doc.exists:
                data = doc.to_dict()
                print(f"Found existing architecture summary for {repository} in project {self.project_name}", file=sys.stderr)
                return data
            else:
                print(f"No architecture summary found for {repository} in project {self.project_name}", file=sys.stderr)
                return None
        except Exception as e:
            logging.error(f"Error fetching architecture summary: {str(e)}")
            return None
    
    def update_architecture_summary(self, repository, summary, changes_count=0):
        """Update the architecture summary for a repository"""
        try:
            doc_ref = self.db.collection(self.project_name).document('architecture_summaries').collection('summaries').document(repository.replace('/', '_'))
            data = {
                'repository': repository,
                'summary': summary,
                'last_updated': datetime.utcnow(),
                'changes_count': changes_count
            }
            
            doc_ref.set(data, merge=True)


        except Exception as e:
            logging.error(f"Error updating architecture summary: {str(e)}")
            raise
    
    def add_architecture_change(self, repository, pr_number, diff, metadata=None):
        """Add a new architecture change record"""
        try:
            doc_ref = self.db.collection(self.project_name).document('architecture_changes').collection('changes').document()
            change_data = {
                'repository': repository,
                'pr_number': pr_number,
                'diff': diff,
                'timestamp': datetime.utcnow(),
                'metadata': metadata or {}
            }
            doc_ref.set(change_data)
            print(f"Successfully added architecture change for {repository} in project {self.project_name}", file=sys.stderr)
            return doc_ref.id
        except Exception as e:
            logging.error(f"Error adding architecture change: {str(e)}")
            raise
    
    def get_recent_changes(self, repository, limit=10):
        """Get recent architecture changes for context"""
        try:
            query = (self.db.collection(self.project_name).document('architecture_changes').collection('changes')
                    .where(filter=firestore.FieldFilter('repository', '==', repository))
                    .order_by('timestamp', direction=firestore.Query.DESCENDING)
                    .limit(limit))
            
            changes = []
            for doc in query.stream():
                data = doc.to_dict()
                changes.append(data)
            
            print(f"Found {len(changes)} recent changes for {repository} in project {self.project_name}", file=sys.stderr)
            return changes
        except Exception as e:
            logging.error(f"Error getting recent changes: {str(e)}")
            return []
    
    def should_summarize(self, repository, changes_threshold=None):
        """Determine if we should regenerate the architecture summary"""
        if changes_threshold is None:
            # Get from Firebase macros or environment variable
            changes_threshold = self.get_changes_threshold()
            
        try:
            doc_ref = self.db.collection(self.project_name).document('architecture_summaries').collection('summaries').document(repository.replace('/', '_'))
            doc = doc_ref.get()
            
            if not doc.exists:
                print(f"No existing summary found for {repository}, should summarize", file=sys.stderr)
                return True
            
            data = doc.to_dict()
            changes_count = data.get('changes_count', 0)
            should_summarize = changes_count >= changes_threshold
            print(f"Repository {repository} has {changes_count} changes, threshold is {changes_threshold}, should summarize: {should_summarize}", file=sys.stderr)
            return should_summarize
        except Exception as e:
            logging.error(f"Error checking should_summarize: {str(e)}")
            return False
    
    def get_changes_threshold(self):
        """Get the changes threshold from Firebase macros or environment variable"""
        try:
            # First try to get from Firebase using the imported fetch_macros function
            macros = fetch_macros()
            
            if macros and 'CHANGES_THRESHOLD' in macros:
                threshold = macros['CHANGES_THRESHOLD']
                return int(threshold)
            
            # Fallback to environment variable
            env_threshold = os.environ.get('CHANGES_THRESHOLD')
            if env_threshold is not None:
                return int(env_threshold)
            
            # Default fallback
            print("No CHANGES_THRESHOLD found in Firebase or environment, using default: 5", file=sys.stderr)
            return 5
            
        except (ValueError, TypeError) as e:
            logging.error(f"Error parsing CHANGES_THRESHOLD: {str(e)}")
            return 5
