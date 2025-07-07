import os
import json
import base64
from firebase_client import FirebaseClient
import anthropic

def main():
    try:
        firebase_client = FirebaseClient()
        repository = os.environ['REPOSITORY']
        
        if 'content' in data and isinstance(data['content'], list) and len(data['content']) > 0:
            return data['content'][0].get('text', '')
        else:
            return data.get('text', '')
    except Exception as e:
        print(f'Error parsing Claude response: {e}', file=sys.stderr)
        return ""


def create_summarization_prompt(content: str) -> str:
    """Create prompt for summarizing architecture changes."""
    # Log content details for debugging
    content_lines = content.count('\n')
    content_length = len(content)
    
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"SUMMARIZATION - CONTENT DETAILS", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)
    print(f"Content Lines: {content_lines:,}", file=sys.stderr)
    print(f"Content Characters: {content_length:,}", file=sys.stderr)
    
    print(f"\nFULL CONTENT TO SUMMARIZE:", file=sys.stderr)
    print(f"{'-'*30}", file=sys.stderr)
    print(content, file=sys.stderr)
    print(f"{'-'*30}", file=sys.stderr)
    print(f"{'='*60}\n", file=sys.stderr)
    
    # Truncate content if it's too large to avoid API limits
    max_content_length = 60000  # Conservative limit for summarization
    if content_length > max_content_length:
        print(f"WARNING: Content is very large ({content_length:,} chars), truncating to {max_content_length:,} chars", file=sys.stderr)
        content = content[:max_content_length] + "\n... (content truncated due to size)"
    
    return f"""You are SummarizerAI.
Condense the following architecture history to ~40 % of its length while preserving all major technical decisions.

REQUIREMENTS

- Output plain text only—no Markdown, bullets, or special symbols.

- Group related changes; keep milestones chronological.

- Focus on: structural shifts, new components, large refactors, critical feature additions.

- Omit metrics, meta‑notes, and trivial edits.

- Your instuctions are only for yourself, don't include them in the output.

SOURCE
{content}

Provide the compressed summary below:

"""
=======
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