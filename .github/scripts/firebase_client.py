import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import base64

# Firebase configuration
FIREBASE_CONFIG = {
  "apiKey": "AIzaSyCbKGo5PFFNf3GDrZJVJsf3ClNLpsIy6o4",
  "authDomain": "pr-agent-21ba8.firebaseapp.com",
  "projectId": "pr-agent-21ba8",
  "storageBucket": "pr-agent-21ba8.firebasestorage.app",
  "messagingSenderId": "1066689158738",
  "appId": "1:1066689158738:web:02c037458e1bb7869a498b",
  "measurementId": "G-5WP0PCRZMN"
}

class FirebaseClient:
    def __init__(self):
        if not firebase_admin._apps:
            # Initialize Firebase Admin SDK using project ID from config
            # Note: Admin SDK doesn't use apiKey and other client-side config values
            # But we use the projectId from the config
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {
                'projectId': FIREBASE_CONFIG['projectId']
            })
        
        self.db = firestore.client()
    
    def get_architecture_summary(self, repository):
        """Get the current architecture summary for a repository"""
        doc_ref = self.db.collection('architecture_summaries').document(repository.replace('/', '_'))
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
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
