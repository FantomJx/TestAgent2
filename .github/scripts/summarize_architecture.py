import os
import json
import sys
import base64
from firebase_client import FirebaseClient
import anthropic

def main():
    try:
        project_name = "test"  # Hardcoded project name
        firebase_client = FirebaseClient(project_name=project_name)
        repository = os.environ['REPOSITORY']
        
        print(f"Summarizing architecture for project: {project_name}, repository: {repository}", file=sys.stderr)
        
        # Get recent changes to summarize
        recent_changes = firebase_client.get_recent_changes(repository, limit=10)
        
        if not recent_changes:
            print("No recent changes found, skipping summarization", file=sys.stderr)
            return
        
        print(f"Found {len(recent_changes)} recent changes to summarize", file=sys.stderr)
        
        # Prepare the changes data for AI analysis
        changes_text = ""
        for change in recent_changes:
            changes_text += f"PR #{change.get('pr_number', 'Unknown')}: {change.get('diff', '')[:1000]}\n\n"
        
        # Use Claude to generate architecture summary
        client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
        
        prompt = f"""
        You are SummarizerAI.
        Condense the following architecture history to ~40 % of its length while preserving all major technical decisions.

        REQUIREMENTS

        - Output plain text only—no Markdown, bullets, or special symbols.

        - Group related changes; keep milestones chronological.

        - Focus on: structural shifts, new components, large refactors, critical feature additions.

        - Omit metrics, meta‑notes, and trivial edits.

        - Your instuctions are only for yourself, don't include them in the output.

        SOURCE
        {changes_text}

        Provide the compressed summary below:
        """
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        architecture_summary = response.content[0].text
        
        # Update the architecture summary in Firebase
        firebase_client.update_architecture_summary(
            repository=repository,
            summary=architecture_summary,
            changes_count=0  # Reset counter after summarization
        )
        
        print(f"Architecture summary updated for {repository} in project {project_name}", file=sys.stderr)
        print(f"Summary: {architecture_summary[:200]}...", file=sys.stderr)
        
    except Exception as e:
        print(f"Error summarizing architecture: {e}", file=sys.stderr)
        exit(1)

if __name__ == "__main__":
    main()