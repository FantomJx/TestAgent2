import json
import os
import sys
import subprocess
import base64
from datetime import datetime


def create_claude_payload(model: str, prompt: str) -> dict:
    """Create payload for Claude API."""
    return {
        "model": model,
        "max_tokens": 4000,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }


def call_claude_api(api_key: str, payload: dict) -> str:
    """Call Claude API and return the response content."""
    with open('/tmp/claude_summarize_payload.json', 'w') as f:
        json.dump(payload, f)
    
    result = subprocess.run([
        'curl', '-s', 'https://api.anthropic.com/v1/messages',
        '-H', f'x-api-key: {api_key}',
        '-H', 'anthropic-version: 2023-06-01',
        '-H', 'Content-Type: application/json',
        '-d', '@/tmp/claude_summarize_payload.json'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f'Claude API call failed: {result.stderr}', file=sys.stderr)
        return ""
    
    try:
        data = json.loads(result.stdout)
        if 'error' in data:
            print(f'Claude API Error: {data["error"]}', file=sys.stderr)
            return ""
        
        if 'content' in data and isinstance(data['content'], list) and len(data['content']) > 0:
            return data['content'][0].get('text', '')
        else:
            return data.get('text', '')
    except Exception as e:
        print(f'Error parsing Claude response: {e}', file=sys.stderr)
        return ""


def create_summarization_prompt(content: str) -> str:
    """Create prompt for summarizing architecture changes."""
    return f"""You are tasked with summarizing a long architecture change summary file. This file tracks significant changes to a codebase over time.

Please create a concise summary that:
1. Preserves the most important architectural decisions and changes
2. Groups similar changes together
3. Maintains chronological context for major milestones
4. Reduces the total length by at least 60% while keeping essential information
5. Focuses on structural changes, new components, major refactoring, and significant feature additions

The summary should start with a header explaining it's a condensed version, followed by the key architectural evolution points.

Original content to summarize:
{content}

Please provide a well-structured, concise summary:"""


def summarize_architecture_file(file_path: str = "architecture_summary.txt"):
    """Summarize the architecture file using Claude."""
    # Use relative path from current working directory
    if not os.path.exists(file_path):
        print(f"Architecture file {file_path} does not exist", file=sys.stderr)
        return False
    
    # Read current content
    with open(file_path, 'r') as f:
        content = f.read()
    
    api_key = os.environ.get('ANTHROPIC_API_KEY', '')
    if not api_key:
        print('ANTHROPIC_API_KEY not found', file=sys.stderr)
        return False
    
    # Create summarization prompt
    prompt = create_summarization_prompt(content)
    payload = create_claude_payload("claude-sonnet-4-20250514", prompt)
    
    # Get summary from Claude
    summary = call_claude_api(api_key, payload)
    
    if not summary:
        print("Failed to generate summary", file=sys.stderr)
        return False
    
    # Create backup of original with relative path
    backup_path = f"{file_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    with open(backup_path, 'w') as f:
        f.write(content)
    print(f"Created backup: {backup_path}")
    
    # Write summarized content
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_content = f"""# Architecture Change Summary
# This file tracks significant changes to the codebase architecture
# Last summarized: {timestamp}

{summary}

"""
    
    with open(file_path, 'w') as f:
        f.write(new_content)
    
    print(f"Architecture file summarized successfully")
    return True


def main():
    """Main function to summarize architecture file."""
    should_summarize = os.environ.get('SHOULD_SUMMARIZE', 'false').lower() == 'true'
    
    if should_summarize:
        success = summarize_architecture_file()
        if success:
            print("Architecture file summarized successfully")
        else:
            print("Failed to summarize architecture file", file=sys.stderr)
            sys.exit(1)
    else:
        print("Summarization not needed")


if __name__ == "__main__":
    main()
