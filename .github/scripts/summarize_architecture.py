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
        "max_tokens": 10000,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }


def call_claude_api(api_key: str, payload: dict) -> str:
    """Call Claude API and return the response content."""
    # Log payload details before making the API call
    payload_str = json.dumps(payload, indent=2)
    payload_size = len(payload_str)
    prompt_content = payload.get('messages', [{}])[0].get('content', '')
    prompt_length = len(prompt_content)
    
    print(f"\n{'='*80}", file=sys.stderr)
    print(f"CLAUDE API CALL (Summarization)", file=sys.stderr)
    print(f"{'='*80}", file=sys.stderr)
    print(f"Model: {payload.get('model', 'unknown')}", file=sys.stderr)
    print(f"Payload size: {payload_size:,} bytes", file=sys.stderr)
    print(f"Prompt length: {prompt_length:,} characters", file=sys.stderr)
    print(f"Max tokens: {payload.get('max_tokens', 'unknown')}", file=sys.stderr)
    
     # Log warning if payload is very large
    if payload_size > 100000:  # 100k bytes
        print(f"WARNING: Large payload detected ({payload_size:,} bytes)", file=sys.stderr)

    if prompt_length > 5000:  # 5k characters
        print(f"WARNING: Very long prompt detected ({prompt_length:,} characters)", file=sys.stderr)
    
    print(f"\nFULL PAYLOAD BEING SENT:", file=sys.stderr)
    print(f"{'-'*40}", file=sys.stderr)
    print(payload_str, file=sys.stderr)
    print(f"{'-'*40}", file=sys.stderr)
    
    print(f"\nFULL PROMPT CONTENT:", file=sys.stderr)
    print(f"{'-'*40}", file=sys.stderr)
    print(prompt_content, file=sys.stderr)
    print(f"{'-'*40}", file=sys.stderr)
    print(f"{'='*80}\n", file=sys.stderr)
    
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
    
    return f"""You are tasked with summarizing a long architecture change summary file. This file tracks significant changes to a codebase over time.

Please create a concise summary that:
1. Uses ONLY plain text formatting - no markdown, no asterisks, no bold, no italics
2. Preserves the most important architectural decisions and changes
3. Groups similar changes together
4. Maintains chronological context for major milestones
5. Reduces the total length by at least 60% while keeping essential information
6. Focuses on structural changes, new components, major refactoring, and significant feature additions
7. Excludes summary statistics, notes, and meta-commentary
8. Uses simple section headers without special formatting

The summary should be clean, simple text organized by development phases and time periods.

Original content to summarize:
{content}

Please provide a well-structured, concise summary using only plain text formatting:"""


def summarize_architecture_file(file_path: str = "architecture_summary.txt"):
    """Summarize the architecture file using Claude."""
    # Use relative path from current working directory
    if not os.path.exists(file_path):
        print(f"Architecture file {file_path} does not exist", file=sys.stderr)
        os.create_file(file_path)
    
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