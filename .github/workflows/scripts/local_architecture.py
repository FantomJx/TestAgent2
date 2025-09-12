import os
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional

class LocalArchitectureManager:
    """Manages local architecture summary files in the repository."""
    
    def __init__(self, repo_root: str = None):
        """Initialize with repository root path."""
        if repo_root is None:
            # Default to the repository root (go up from scripts directory)
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
        
        self.repo_root = repo_root
        self.architecture_file = os.path.join(repo_root, ".github", "architecture-summary.json")
        
        # Ensure the .github directory exists
        github_dir = os.path.dirname(self.architecture_file)
        os.makedirs(github_dir, exist_ok=True)
    
    def read_architecture_summary(self) -> Optional[Dict[str, Any]]:
        """Read the local architecture summary file."""
        try:
            if os.path.exists(self.architecture_file):
                with open(self.architecture_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"Read local architecture summary from {self.architecture_file}", file=sys.stderr)
                return data
            else:
                print(f"No local architecture summary found at {self.architecture_file}", file=sys.stderr)
                return None
        except Exception as e:
            print(f"Error reading local architecture summary: {e}", file=sys.stderr)
            return None
    
    def write_architecture_summary(self, repository: str, summary: str) -> bool:
        """Write architecture summary to local file."""
        try:
            data = {
                'repository': repository,
                'summary': summary,
                'last_updated': datetime.utcnow().isoformat(),
                'source': 'local'
            }
            
            with open(self.architecture_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"Wrote local architecture summary to {self.architecture_file}", file=sys.stderr)
            return True
        except Exception as e:
            print(f"Error writing local architecture summary: {e}", file=sys.stderr)
            return False
    
    def add_architecture_change(self, pr_number: int, diff: str, metadata: Dict[str, Any] = None) -> Optional[str]:
        """Add architecture change to local tracking (simplified version)."""
        try:
            changes_file = os.path.join(self.repo_root, ".github", "architecture-changes.json")
            
            # Read existing changes
            changes = []
            if os.path.exists(changes_file):
                try:
                    with open(changes_file, 'r', encoding='utf-8') as f:
                        changes = json.load(f)
                except Exception as e:
                    print(f"Warning: Could not read existing changes file: {e}", file=sys.stderr)
                    changes = []
            
            # Add new change
            change_id = f"local_{pr_number}_{int(datetime.utcnow().timestamp())}"
            change_entry = {
                'id': change_id,
                'pr_number': pr_number,
                'timestamp': datetime.utcnow().isoformat(),
                'diff_size': len(diff),
                'metadata': metadata or {}
            }
            
            # Keep only recent changes (last 10)
            changes.append(change_entry)
            changes = sorted(changes, key=lambda x: x['timestamp'], reverse=True)[:10]
            
            # Write back
            with open(changes_file, 'w', encoding='utf-8') as f:
                json.dump(changes, f, indent=2, ensure_ascii=False)
            
            print(f"Added local architecture change: {change_id}", file=sys.stderr)
            return change_id
            
        except Exception as e:
            print(f"Error adding local architecture change: {e}", file=sys.stderr)
            return None
    
    def get_recent_changes(self, limit: int = 5) -> list:
        """Get recent architecture changes from local file."""
        try:
            changes_file = os.path.join(self.repo_root, ".github", "architecture-changes.json")
            
            if os.path.exists(changes_file):
                with open(changes_file, 'r', encoding='utf-8') as f:
                    changes = json.load(f)
                
                # Return most recent changes
                changes = sorted(changes, key=lambda x: x['timestamp'], reverse=True)
                return changes[:limit]
            else:
                return []
        except Exception as e:
            print(f"Error reading local architecture changes: {e}", file=sys.stderr)
            return []
    
    def should_summarize(self, diff_size: int = 0, pr_description: str = '') -> bool:
        """Simple heuristic for whether to regenerate summary (simplified version)."""
        # For local version, use simple heuristics
        # Summarize if diff is large or PR description mentions architecture
        large_diff_threshold = 5000  # characters
        architecture_keywords = ['architecture', 'refactor', 'restructure', 'migration']
        
        if diff_size > large_diff_threshold:
            return True
        
        if any(keyword in pr_description.lower() for keyword in architecture_keywords):
            return True
        
        return False


def create_hybrid_context(repository: str, local_manager: LocalArchitectureManager, firebase_client=None) -> Dict[str, Any]:
    """Create architecture context using local files first, Firebase as fallback."""
    context = {
        'architecture_summary': None,
        'recent_changes': [],
        'repository': repository,
        'source': 'none'
    }
    
    # Try local first
    local_summary = local_manager.read_architecture_summary()
    local_changes = local_manager.get_recent_changes()
    
    if local_summary:
        context['architecture_summary'] = local_summary
        context['source'] = 'local'
        print("Using local architecture summary", file=sys.stderr)
    elif firebase_client:
        # Fallback to Firebase
        try:
            firebase_summary = firebase_client.get_architecture_summary(repository)
            if firebase_summary:
                context['architecture_summary'] = firebase_summary
                context['source'] = 'firebase'
                print("Using Firebase architecture summary (local not available)", file=sys.stderr)
        except Exception as e:
            print(f"Firebase fallback failed: {e}", file=sys.stderr)
    
    # Use local changes if available
    if local_changes:
        context['recent_changes'] = local_changes
        print(f"Using {len(local_changes)} local architecture changes", file=sys.stderr)
    elif firebase_client:
        # Could add Firebase recent changes fallback here if needed
        pass
    
    return context
