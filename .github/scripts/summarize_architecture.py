import os
import json
import base64
from firebase_client import FirebaseClient
import anthropic

def main():
    try:
        firebase_client = FirebaseClient()
        repository = os.environ['REPOSITORY']
        
        # Get recent changes to summarize
        recent_changes = firebase_client.get_recent_changes(repository, limit=10)
        
        if not recent_changes:
            print("No recent changes found, skipping summarization")
            return
        
        # Prepare the changes data for AI analysis
        changes_text = ""
        for change in recent_changes:
            changes_text += f"PR #{change.get('pr_number', 'Unknown')}: {change.get('diff', '')[:1000]}\n\n"
        
        # Use Claude to generate architecture summary
        client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
        
        prompt = f"""
        You are SummarizerAI.
        Condense the following architecture history to ~40 % of its length while preserving all major technical decisions.

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
        
        print(f"Architecture summary updated for {repository}")
        
    except Exception as e:
        print(f"Error summarizing architecture: {e}")
        exit(1)

if __name__ == "__main__":
    main()