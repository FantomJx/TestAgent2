import json
import os
import sys
import subprocess
from typing import List, Dict, Any


def read_architecture_context() -> str:
    """Read the architecture summary file for context."""
    file_path = "architecture_summary.txt"  # Use relative path
    
    if not os.path.exists(file_path):
        return "No existing architecture summary available."
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            # Limit context to avoid token limits
            words = content.split()
            if len(words) > 1500:  # Limit to ~1500 words
                content = ' '.join(words[:1500]) + "\n... (truncated for brevity)"
            return content
    except Exception as e:
        print(f'Error reading architecture summary: {e}', file=sys.stderr)
        return "Error reading architecture summary."


def create_claude_payload(model: str, prompt: str) -> Dict[str, Any]:
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


def create_openai_payload(model: str, prompt: str) -> Dict[str, Any]:
    """Create payload for OpenAI API."""
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


def call_claude_api(api_key: str, payload: Dict[str, Any]) -> str:
    """Call Claude API and return the response content."""
    # Log payload details before making the API call
    payload_str = json.dumps(payload, indent=2)
    payload_size = len(payload_str)
    prompt_content = payload.get('messages', [{}])[0].get('content', '')
    prompt_length = len(prompt_content)
    
    print(f"\n{'='*80}", file=sys.stderr)
    print(f"CLAUDE API CALL (AI Review)", file=sys.stderr)
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
    
    with open('/tmp/claude_payload.json', 'w') as f:
        json.dump(payload, f)
    
    result = subprocess.run([
        'curl', '-s', 'https://api.anthropic.com/v1/messages',
        '-H', f'x-api-key: {api_key}',
        '-H', 'anthropic-version: 2023-06-01',
        '-H', 'Content-Type: application/json',
        '-d', '@/tmp/claude_payload.json'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f'Claude API call failed: {result.stderr}', file=sys.stderr)
        return '[]'
    
    print(f"Claude API response status: success", file=sys.stderr)
    
    try:
        data = json.loads(result.stdout)
        if 'error' in data:
            error_info = data['error']
            error_type = error_info.get('type', 'unknown')
            error_message = error_info.get('message', 'unknown error')
            print(f'Claude API Error - Type: {error_type}, Message: {error_message}', file=sys.stderr)
            
            # Check for common payload size related errors
            if 'too_large' in error_message.lower() or 'limit' in error_message.lower():
                print(f'ERROR: Payload may be too large for Claude API', file=sys.stderr)
            
            return '[]'
            return '[]'
        
        if 'content' in data and isinstance(data['content'], list) and len(data['content']) > 0:
            return data['content'][0].get('text', '[]')
        else:
            return data.get('text', '[]')
    except Exception as e:
        print(f'Error parsing Claude response: {e}', file=sys.stderr)
        return '[]'


def call_openai_api(api_key: str, payload: Dict[str, Any]) -> str:
    """Call OpenAI API and return the response content."""
    with open('/tmp/openai_payload.json', 'w') as f:
        json.dump(payload, f)
    
    result = subprocess.run([
        'curl', '-s', 'https://api.openai.com/v1/chat/completions',
        '-H', f'Authorization: Bearer {api_key}',
        '-H', 'Content-Type: application/json',
        '-d', '@/tmp/openai_payload.json'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f'OpenAI API call failed: {result.stderr}', file=sys.stderr)
        return '[]'
    
    try:
        data = json.loads(result.stdout)
        if 'error' in data:
            print(f'OpenAI API Error: {data["error"]}', file=sys.stderr)
            return '[]'
        
        return data.get('choices', [{}])[0].get('message', {}).get('content', '[]')
    except Exception as e:
        print(f'Error parsing OpenAI response: {e}', file=sys.stderr)
        return '[]'


def create_review_prompt(diff: str) -> str:
    """Create the review prompt for the AI model."""
    architecture_context = read_architecture_context()
    
    # Log diff details for debugging
    diff_lines = diff.count('\n')
    diff_length = len(diff)
    
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"AI REVIEW - DIFF DETAILS", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)
    print(f"Diff Lines: {diff_lines:,}", file=sys.stderr)
    print(f"Diff Characters: {diff_length:,}", file=sys.stderr)
    
    print(f"\nFULL DIFF CONTENT:", file=sys.stderr)
    print(f"{'-'*30}", file=sys.stderr)
    print(diff, file=sys.stderr)
    print(f"{'-'*30}", file=sys.stderr)
    
    print(f"\nARCHITECTURE CONTEXT:", file=sys.stderr)
    print(f"{'-'*30}", file=sys.stderr)
    print(architecture_context, file=sys.stderr)
    print(f"{'-'*30}", file=sys.stderr)
    print(f"{'='*60}\n", file=sys.stderr)
    
    # Truncate diff if it's too large to avoid API limits
    max_diff_length = 80000  # Conservative limit for diff content
    if diff_length > max_diff_length:
        print(f"WARNING: Diff is very large ({diff_length:,} chars), truncating to {max_diff_length:,} chars", file=sys.stderr)
        diff = diff[:max_diff_length] + "\n... (diff truncated due to size)"
    
    return f"""You are a helpful and diligent code assistant. Review the following unified diff and provide line-by-line feedback for specific issues.

ARCHITECTURE CONTEXT:
The following is a summary of significant architectural changes made to this codebase over time. Use this context to ensure your review considers how the current changes fit with the existing architecture:

{architecture_context}

---

CRITICAL: Only comment on lines that are ADDED (marked with +) or MODIFIED in the diff. Do NOT comment on unchanged lines or lines that are removed (marked with -).

IMPORTANT: Return ONLY a valid JSON array of objects. Each object should have exactly these fields:
- "path": the file path relative to repo root (exactly as shown in the diff header)
- "line": the line number in the NEW file (after changes) - this must be a line that was added or modified
- "comment": a short, actionable comment about the specific issue

Consider the architectural context when reviewing. Focus on:
1. Consistency with existing patterns and architecture
2. Potential conflicts with previous architectural decisions
3. Whether new changes align with the established codebase structure
4. Security, performance, and maintainability issues

Only comment on lines that have actual issues (bugs, security problems, performance issues, or significant improvements). Focus on ADDED lines (marked with +) in the diff. Return an empty array [] if no issues are found.

Example format:
[
  {{"path": "src/file.js", "line": 15, "comment": "Consider null check before accessing property"}},
  {{"path": "src/file.js", "line": 23, "comment": "Use const instead of let for immutable variable"}}
]

Diff to review:
```diff
{diff}
```"""


def get_ai_review(model: str, diff: str) -> str:
    """Get AI review for the given diff using specified model."""
    prompt = create_review_prompt(diff)
    
    if model == "claude-sonnet-4-20250514":
        api_key = os.environ.get('ANTHROPIC_API_KEY', '')
        if not api_key:
            print('ANTHROPIC_API_KEY not found', file=sys.stderr)
            return '[]'
        
        payload = create_claude_payload(model, prompt)
        return call_claude_api(api_key, payload)
    else:
        api_key = os.environ.get('OPENAI_API_KEY', '')
        if not api_key:
            print('OPENAI_API_KEY not found', file=sys.stderr)
            return '[]'
        
        payload = create_openai_payload(model, prompt)
        return call_openai_api(api_key, payload)


def filter_github_files_from_diff(diff: str) -> str:
    """Filter out .github files from the diff content."""
    lines = diff.split('\n')
    filtered_lines = []
    skip_file = False
    
    for line in lines:
        if line.startswith('diff --git'):
            # Check if this is a .github file
            parts = line.split()
            if len(parts) >= 4:
                file_path = parts[3][2:]  # Remove "b/" prefix
                if file_path.startswith('.github/'):
                    skip_file = True
                    print(f"Filtering out .github file from AI review: {file_path}", file=sys.stderr)
                    continue
                else:
                    skip_file = False
        
        if not skip_file:
            filtered_lines.append(line)
    
    return '\n'.join(filtered_lines)


if __name__ == "__main__":
    # Get environment variables
    diff_b64 = os.environ.get('DIFF_B64', '')
    model = os.environ.get('MODEL', '')
    
    if not diff_b64 or not model:
        print('Missing required environment variables', file=sys.stderr)
        sys.exit(1)
    
    # Decode diff
    import base64
    diff = base64.b64decode(diff_b64).decode('utf-8')
    
    # Filter out .github files from diff
    diff = filter_github_files_from_diff(diff)
    
    # Check if there's any meaningful diff left after filtering
    if not diff.strip() or not any(line.startswith('diff --git') for line in diff.split('\n')):
        print("No significant files to analyze after filtering .github files", file=sys.stderr)
        review_b64 = base64.b64encode("[]".encode('utf-8')).decode('utf-8')
        print(f"review_b64={review_b64}")
        sys.exit(0)
    
    # Get review
    review = get_ai_review(model, diff)
    
    # Output base64 encoded review
    review_b64 = base64.b64encode(review.encode('utf-8')).decode('utf-8')
    print(f"review_b64={review_b64}")