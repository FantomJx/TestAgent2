from cost_tracker import CostTracker
import json
import os
import sys
import subprocess
from typing import List, Dict, Any
import base64

# Add the scripts directory to the path for importing cost_tracker
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def read_architecture_context() -> str:
    """Read the architecture summary from Firebase context."""
    # Get architecture context from Firebase (via environment variable)
    architecture_context_b64 = os.environ.get('ARCHITECTURE_CONTEXT_B64')
    
    if not architecture_context_b64:
        return "No architecture summary available."
    
    try:
        context_json = base64.b64decode(architecture_context_b64).decode('utf-8')
        architecture_context = json.loads(context_json)
        architecture_summary = architecture_context.get(
            'architecture_summary', {}).get('summary', '')
        recent_changes_context = ""
        recent_changes = architecture_context.get('recent_changes', [])[
            :3]  # Limit to 3 most recent
        for change in recent_changes:
            recent_changes_context += f"Recent PR #{change.get('pr_number', 'Unknown')}: {change.get('metadata', {}).get('pr_title', 'No title')}\n"
        return f"{architecture_summary}\n\n{recent_changes_context}"
    except Exception as e:
        print(
            f"Warning: Could not decode architecture context: {e}", file=sys.stderr)
        return "Error decoding architecture context."


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





def call_claude_api(api_key: str, payload: Dict[str, Any]) -> str:
    """Call Claude API and return the response content."""
    # Log minimal payload details
    payload_size = len(json.dumps(payload))
    prompt_length = len(payload.get('messages', [{}])[0].get('content', ''))

    print(
        f"Claude API call - Model: {payload.get('model', 'unknown')}", file=sys.stderr)

    # Log warning if payload is very large
    if payload_size > 100000:  # 100k bytes
        print(
            f"WARNING: Large payload detected ({payload_size:,} bytes)", file=sys.stderr)

    if prompt_length > 600000:  # 5k characters
        print(
            f"WARNING: Very long prompt detected ({prompt_length:,} characters)", file=sys.stderr)

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
            print(
                f'Claude API Error - Type: {error_type}, Message: {error_message}', file=sys.stderr)

            # Check for common payload size related errors
            if 'too_large' in error_message.lower() or 'limit' in error_message.lower():
                print(f'ERROR: Payload may be too large for Claude API',
                      file=sys.stderr)

            return '[]'

        # Track cost before returning
        try:
            cost_tracker = CostTracker()
            cost_tracker.track_api_call(
                model=payload.get('model', 'claude-sonnet-4-20250514'),
                response_data=data,
                call_type="review",
                context="Code review analysis"
            )
        except Exception as e:
            print(f"Warning: Cost tracking failed: {e}", file=sys.stderr)

        if 'content' in data and isinstance(data['content'], list) and len(data['content']) > 0:
            return data['content'][0].get('text', '[]')
        else:
            return data.get('text', '[]')
    except Exception as e:
        print(f'Error parsing Claude response: {e}', file=sys.stderr)
        return '[]'





def create_review_prompt(diff: str) -> str:
    """Create the review prompt for the AI model."""
    architecture_context = read_architecture_context()

    # Get custom AI prompt from environment
    custom_ai_prompt = os.environ.get('CUSTOM_AI_PROMPT', '').strip()

    # Log minimal diff details
    diff_lines = diff.count('\n')
    diff_length = len(diff)
    print(
        f"Diff size: {diff_lines:,} lines, {diff_length:,} characters", file=sys.stderr)

    if custom_ai_prompt:
        print(
            f"Using custom AI prompt: {custom_ai_prompt[:100]}{'...' if len(custom_ai_prompt) > 100 else ''}", file=sys.stderr)

    # Truncate diff if it's too large to avoid API limits
    max_diff_length = 1500000  # Maximum safe limit for Claude Sonnet 4
    if diff_length > max_diff_length:
        print(
            f"WARNING: Diff is very large ({diff_length:,} chars), truncating to {max_diff_length:,} chars", file=sys.stderr)
        diff = diff[:max_diff_length] + "\n... (diff truncated due to size)"

    # Build the base prompt
    base_prompt = f"""You are a helpful and diligent code assistant. Review the following unified diff and provide line-by-line feedback for specific issues.

    TASK
    Review the unified diff below and return feedback **only** on lines that were *added* or *modified*.

    ARCHITECTURE CONTEXT
    {architecture_context}"""

    # Add custom prompt if provided
    if custom_ai_prompt:
        base_prompt += f"""

    CUSTOM REVIEW INSTRUCTIONS
    {custom_ai_prompt}"""

    # Add the rest of the prompt
    base_prompt += f"""

    OUTPUT
    Return a JSON array.  Each element **must** follow this exact schema:
    {{
        "path": "<file path from diff header>",
        "line": <line number in the *new* file>,
        "comment": "<concise actionable issue>"
    }}
    Return `[]` if no issues.

    COMMENT‑WORTHY ISSUES
    - Bugs / logic errors
    - Security vulnerabilities
    - Performance or memory leaks
    - Maintainability / readability problems
    - Violations of existing architectural patterns

    RULES
    1. Comment only on `+` lines (added or modified).
    2. Skip unchanged (` `) and removed (`-`) lines.
    3. One problem → one JSON object.  No duplicates.
    4. Keep comments short (<20 words) and specific.
    5. Do not wrap output in Markdown or extra text—*JSON only*.
    6. Be extremely concise and avoid unnecessary verbosity in output.

    DIFF TO REVIEW
    ```diff
    {diff}
```"""

    return base_prompt





def get_ai_review(model: str, diff: str) -> str:
    """Get AI review for the given diff using Claude model."""
    prompt = create_review_prompt(diff)
    
    api_key = os.environ.get('ANTHROPIC_API_KEY', '')
    if not api_key:
        print('ANTHROPIC_API_KEY not found', file=sys.stderr)
        return '[]'

    payload = create_claude_payload(model, prompt)
    return call_claude_api(api_key, payload)


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
                    print(
                        f"Filtering out .github file from AI review: {file_path}", file=sys.stderr)
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
    has_important_label = os.environ.get(
        'HAS_IMPORTANT_LABEL', 'false').lower() == 'true'


    if not diff_b64:
        print('Missing required environment variable: DIFF_B64', file=sys.stderr)
        sys.exit(1)

    # Decode diff
    diff = base64.b64decode(diff_b64).decode('utf-8')

    # Filter out .github files from diff
    diff = filter_github_files_from_diff(diff)

    # Check if there's any meaningful diff left after filtering
    if not diff.strip() or not any(line.startswith('diff --git') for line in diff.split('\n')):
        print(
            "No significant files to analyze after filtering .github files", file=sys.stderr)
        review_b64 = base64.b64encode("[]".encode('utf-8')).decode('utf-8')

        # Write output to GitHub Actions output file (strip any carriage returns)
        if 'GITHUB_OUTPUT' in os.environ:
            clean_review_b64 = str(review_b64).replace('\r', '').replace('\n', '')
            with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
                fh.write(f"review_b64={clean_review_b64}\n")
        else:
            # Fallback for local testing
            print(f"review_b64={review_b64}", file=sys.stderr)
        sys.exit(0)

    # Always use Claude model
    selected_model = "claude-sonnet-4-20250514"
    model_comment = "This response was generated by Claude 4 Sonnet."

    # Override with provided model if specified (must be a Claude model)
    if model and model.startswith('claude'):
        selected_model = model
        print(f"Using Claude model override: {selected_model}", file=sys.stderr)
    elif model and not model.startswith('claude'):
        print(f"Warning: Non-Claude model '{model}' requested, using Claude instead", file=sys.stderr)

    print(f"Selected model: {selected_model}", file=sys.stderr)

    # Get review
    review = get_ai_review(selected_model, diff)

    # Output base64 encoded review and model info
    review_b64 = base64.b64encode(review.encode('utf-8')).decode('utf-8')

    # Write output to GitHub Actions output file (strip any carriage returns)
    if 'GITHUB_OUTPUT' in os.environ:
        clean_review_b64 = str(review_b64).replace('\r', '').replace('\n', '')
        clean_model_used = str(selected_model).replace('\r', '').replace('\n', ' ')
        clean_model_comment = str(model_comment).replace('\r', '').replace('\n', ' ')
        with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
            fh.write(f"review_b64={clean_review_b64}\n")
            fh.write(f"model_used={clean_model_used}\n")
            fh.write(f"model_comment={clean_model_comment}\n")
    else:
        # Fallback for local testing
        print(f"review_b64={review_b64}", file=sys.stderr)
        print(f"model_used={selected_model}", file=sys.stderr)
        print(f"model_comment={model_comment}", file=sys.stderr)
