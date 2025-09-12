import os
import json
import sys
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import base64
import logging

from config import PROJECT_NAME

class FirebaseClient:
    def __init__(self, service_account_json=None, project_name=None):
        try:
            if not firebase_admin._apps:
                # Use provided JSON string or get from environment variable
                if not service_account_json:
                    service_account_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT_JSON')
                
                if not service_account_json:
                    raise ValueError("Firebase service account JSON not provided via parameter or FIREBASE_SERVICE_ACCOUNT_JSON environment variable")
                
                # Parse the JSON string into a dictionary
                try:
                    service_account_info = json.loads(service_account_json)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON in Firebase service account credentials: {str(e)}")
                    
                cred = credentials.Certificate(service_account_info)
                firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
            # Use the provided project name or fall back to the global config
            self.project_name = project_name if project_name is not None else PROJECT_NAME
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
                return data
            else:
                return None
        except Exception as e:
            logging.error(f"Error fetching architecture summary: {str(e)}")
            return None
    
    def update_architecture_summary(self, repository, summary):
        """Update the architecture summary for a repository"""
        try:
            doc_ref = self.db.collection(self.project_name).document('architecture_summaries').collection('summaries').document(repository.replace('/', '_'))
            data = {
                'repository': repository,
                'summary': summary,
                'last_updated': datetime.utcnow()
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
            
            return changes
        except Exception as e:
            logging.error(f"Error getting recent changes: {str(e)}")
            return []
    
    def should_summarize(self, repository, diff_size=0, changes_threshold=None, pr_description=""):
        """Determine if we should regenerate the architecture summary based on existing summary size or PR markers"""
        try:
            doc_ref = self.db.collection(self.project_name).document('architecture_summaries').collection('summaries').document(repository.replace('/', '_'))
            doc = doc_ref.get()
            
            if not doc.exists:
                print("No existing architecture summary - will create one", file=sys.stderr)
                return True  # No existing summary - create one
            
            # Check if PR description contains architecture summary trigger
            if pr_description and self._check_pr_description_for_architecture_trigger(pr_description):
                print("Architecture summary requested in PR description - will regenerate", file=sys.stderr)
                return True
            
            # Check the size of the existing summary
            existing_data = doc.to_dict()
            existing_summary = existing_data.get('summary', '') if existing_data else ''
            summary_size = len(existing_summary)
            
            # Set threshold for "big" summaries that need regeneration
            # Default to 13KB of summary content (getting too long)
            threshold = changes_threshold or 13000  # 13KB
            
            if summary_size >= threshold:
                print(f"Large architecture summary detected ({summary_size} bytes >= {threshold} threshold) - will regenerate summary", file=sys.stderr)
                return True
            else:
                print(f"Architecture summary size OK ({summary_size} bytes < {threshold} threshold) - skipping regeneration", file=sys.stderr)
                return False
                
        except Exception as e:
            logging.error(f"Error checking should_summarize: {str(e)}")
            return False
    
    def _check_pr_description_for_architecture_trigger(self, pr_description):
        """Check if PR description contains markers to trigger architecture summary"""
        if not pr_description:
            return False
            
        # Convert to lowercase for case-insensitive matching
        description_lower = pr_description.lower()
        
        # Check for various trigger patterns
        trigger_patterns = [
            "update architecture summary",
            "regenerate architecture", 
            "refresh architecture",
            "architecture summary",
            "[architecture]",
            "<!-- architecture -->",
            "@architecture-summary"
        ]
        
        for pattern in trigger_patterns:
            if pattern in description_lower:
                print(f"Found architecture trigger pattern: '{pattern}'", file=sys.stderr)
                return True
                
        return False

