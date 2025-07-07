import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import base64
import logging

class FirebaseClient:
    def __init__(self, service_account_path=None):
        try:
            if not firebase_admin._apps:
                # Use provided path or default
                if not service_account_path:
                    service_account_path = os.path.join(
                        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                        "pr-agent-21ba8-firebase-adminsdk-fbsvc-95c716d6e2.json"
                    )
                
                if not os.path.exists(service_account_path):
                    raise FileNotFoundError(f"Firebase credentials file not found at: {service_account_path}")
                    
                cred = credentials.Certificate(service_account_path)
                firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
        except Exception as e:
            logging.error(f"Failed to initialize Firebase: {str(e)}")
            raise
    
    def get_architecture_summary(self, repository):
        """Get the current architecture summary for a repository"""
        if not repository:
            return None
            
        try:
            doc_ref = self.db.collection('architecture_summaries').document(repository.replace('/', '_'))
            doc = doc_ref.get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            logging.error(f"Error fetching architecture summary: {str(e)}")
            return None
    
    def update_architecture_summary(self, repository, summary, changes_count=0):
        """Update the architecture summary for a repository"""
        doc_ref = self.db.collection('architecture_summaries').document(repository.replace('/', '_'))
        doc_ref.set({
            'repository': repository,
            'summary': summary,
            'last_updated': datetime.utcnow(),
            'changes_count': changes_count
        }, merge=True)
    
    def add_architecture_change(self, repository, pr_number, diff, metadata=None):
        """Add a new architecture change record"""
        doc_ref = self.db.collection('architecture_changes').document()
        change_data = {
            'repository': repository,
            'pr_number': pr_number,
            'diff': diff,
            'timestamp': datetime.utcnow(),
            'metadata': metadata or {}
        }
        doc_ref.set(change_data)
        return doc_ref.id
    
    def get_recent_changes(self, repository, limit=10):
        """Get recent architecture changes for context"""
        query = (self.db.collection('architecture_changes')
                .where('repository', '==', repository)
                .order_by('timestamp', direction=firestore.Query.DESCENDING)
                .limit(limit))
        
        changes = []
        for doc in query.stream():
            data = doc.to_dict()
            changes.append(data)
        return changes
    
    def should_summarize(self, repository, changes_threshold=5):
        """Determine if we should regenerate the architecture summary"""
        doc_ref = self.db.collection('architecture_summaries').document(repository.replace('/', '_'))
        doc = doc_ref.get()
        
        if not doc.exists:
            return True
        
        data = doc.to_dict()
        changes_count = data.get('changes_count', 0)
        return changes_count >= changes_threshold
