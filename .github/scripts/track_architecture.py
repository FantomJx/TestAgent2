import json
import os
import sys
import subprocess
import base64
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple


def create_claude_payload(model: str, prompt: str) -> dict:
    """Create payload for Claude API."""
    return {
        "model": model,
        "max_tokens": 2000,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }


def call_claude_api(api_key: str, payload: dict) -> str:
    """Call Claude API and return the response content."""
    with open('/tmp/claude_arch_payload.json', 'w') as f:
        json.dump(payload, f)
    
    result = subprocess.run([
        'curl', '-s', 'https://api.anthropic.com/v1/messages',
        '-H', f'x-api-key: {api_key}',
        '-H', 'anthropic-version: 2023-06-01',
        '-H', 'Content-Type: application/json',
        '-d', '@/tmp/claude_arch_payload.json'
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


def create_architecture_analysis_prompt(diff: str, pr_number: str) -> str:
    """Create prompt for Claude to analyze architectural significance."""
    return f"""You are an expert software architect. Analyze the following diff from PR #{pr_number} and determine its architectural significance and importance.

TASK: Evaluate this diff for architectural relevance and assign an importance score.

Architecturally significant changes include:
HIGH IMPORTANCE (Score 8-10):
- New classes, interfaces, or major data structures
- New modules, packages, or significant file additions
- Changes to core algorithms or business logic
- New dependencies or external integrations
- Database schema changes or migrations
- API changes or new endpoints
- Security-related modifications
- Design pattern implementations or architectural refactoring

MEDIUM IMPORTANCE (Score 5-7):
- Significant function additions or modifications
- Configuration changes that affect system behavior
- Build system or CI/CD modifications
- Performance optimizations
- Error handling improvements
- Code organization restructuring
- New utility functions or helpers
- Documentation that affects architecture understanding

LOW IMPORTANCE (Score 1-4):
- Bug fixes that don't change structure
- Minor refactoring or cleanup
- Style/formatting changes
- Test additions without structural impact
- Comment additions
- Small documentation updates

RESPONSE FORMAT: Return a JSON object with exactly these fields:
- "importance_score": integer from 1-10 (how architecturally important this change is)
- "is_significant": boolean (true if score >= 5, indicating we should track it)
- "summary": string (if significant, provide a concise 2-3 sentence summary; if not significant, return empty string)

We want to capture approximately 50% of PRs by tracking those with importance_score >= 5.

Example responses:
{{"importance_score": 8, "is_significant": true, "summary": "Added new user authentication service with JWT implementation. Introduced Redis caching layer for session management. This establishes a new security architecture pattern for the application."}}

{{"importance_score": 6, "is_significant": true, "summary": "Refactored database connection handling and added connection pooling. This improves performance and sets up better resource management patterns."}}

{{"importance_score": 3, "is_significant": false, "summary": ""}}

Diff to analyze:
```diff
{diff}
```

Respond with only the JSON object:"""


def analyze_architectural_significance(diff: str, pr_number: str) -> Tuple[bool, str]:
    """Use Claude to determine if changes are architecturally significant."""
    api_key = os.environ.get('ANTHROPIC_API_KEY', '')
    if not api_key:
        print('ANTHROPIC_API_KEY not found, falling back to basic analysis', file=sys.stderr)
        return False, ""
    
    prompt = create_architecture_analysis_prompt(diff, pr_number)
    payload = create_claude_payload("claude-sonnet-4-20250514", prompt)
    
    response = call_claude_api(api_key, payload)
    if not response:
        print('Failed to get Claude response, falling back to basic analysis', file=sys.stderr)
        return False, ""
    
    try:
        # Clean the response to extract JSON
        cleaned_response = response.strip()
        if cleaned_response.startswith('```json'):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.endswith('```'):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()
        
        data = json.loads(cleaned_response)
        importance_score = data.get('importance_score', 0)
        is_significant = data.get('is_significant', False)
        summary = data.get('summary', '')
        
        print(f"Claude analysis: importance_score={importance_score}, is_significant={is_significant}", file=sys.stderr)
        
        return is_significant, summary
    except json.JSONDecodeError as e:
        print(f'Failed to parse Claude response as JSON: {e}', file=sys.stderr)
        print(f'Raw response: {response}', file=sys.stderr)
        return False, ""


def get_file_paths_from_diff(diff: str) -> List[str]:
    """Extract file paths from diff."""
    paths = []
    for line in diff.split('\n'):
        if line.startswith('diff --git'):
            # Extract file path from "diff --git a/path b/path"
            parts = line.split()
            if len(parts) >= 4:
                path = parts[3][2:]  # Remove "b/" prefix
                paths.append(path)
    return paths


def generate_architecture_summary(claude_summary: str, file_paths: List[str], pr_number: str) -> str:
    """Generate a formatted summary for the architecture file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    summary = f"\n--- PR #{pr_number} - {timestamp} ---\n"
    summary += f"Files modified: {', '.join(file_paths)}\n"
    summary += f"Architectural changes: {claude_summary}\n"
    
    return summary


def append_to_architecture_file(summary: str, file_path: str = "architecture_summary.txt"):
    """Append summary to architecture file."""
    # Use relative path from current working directory
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            f.write("# Architecture Change Summary\n")
            f.write("# This file tracks significant changes to the codebase architecture\n\n")
    
    with open(file_path, 'a') as f:
        f.write(summary)


def get_word_count(file_path: str) -> int:
    """Get word count of a file."""
    # Use relative path from current working directory
    if not os.path.exists(file_path):
        return 0
    
    with open(file_path, 'r') as f:
        content = f.read()
        return len(content.split())


def handle_git_conflicts():
    """Check for and handle Git conflicts."""
    try:
        # Check if we're in a rebase state
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, cwd='.')
        
        if result.returncode == 0:
            # Look for unmerged files (marked with 'U')
            unmerged = [line for line in result.stdout.split('\n') 
                       if line.startswith('U ')]
            
            if unmerged:
                print(f"Git conflicts detected: {unmerged}", file=sys.stderr)
                return False
        
        return True
    except Exception as e:
        print(f"Error checking Git status: {e}", file=sys.stderr)
        return True  # Continue anyway


def main():
    """Main function to track architectural changes."""
    # Check for Git conflicts first
    if not handle_git_conflicts():
        print("Git conflicts detected, skipping architecture tracking", file=sys.stderr)
        print("arch_updated=false")
        print("should_summarize=false")
        return
    
    # Get environment variables
    diff_b64 = os.environ.get('DIFF_B64', '')
    pr_number = os.environ.get('PR_NUMBER', 'unknown')
    
    if not diff_b64:
        print('DIFF_B64 environment variable not found', file=sys.stderr)
        print("arch_updated=false")
        print("should_summarize=false")
        return
    
    try:
        # Decode diff
        diff = base64.b64decode(diff_b64).decode('utf-8')
        
        # Use Claude to analyze architectural significance
        is_significant, claude_summary = analyze_architectural_significance(diff, pr_number)
        file_paths = get_file_paths_from_diff(diff)
        
        # Generate and append summary if Claude determined it's significant
        if is_significant and claude_summary:
            summary = generate_architecture_summary(claude_summary, file_paths, pr_number)
            append_to_architecture_file(summary)
            print(f"Architecture summary updated: {claude_summary}", file=sys.stderr)
            print("arch_updated=true")
        else:
            print("No significant architectural changes detected by Claude", file=sys.stderr)
            print("arch_updated=false")
        
        # Check if summarization is needed
        word_count = get_word_count("architecture_summary.txt")
        print(f"Architecture file word count: {word_count}", file=sys.stderr)
        
        if word_count > 1000:  # Lowered threshold from 5000 to 1000
            print("Architecture file is large, will trigger summarization", file=sys.stderr)
            print("should_summarize=true")
        else:
            print("should_summarize=false")
            
    except Exception as e:
        print(f"Error in architecture tracking: {e}", file=sys.stderr)
        print("arch_updated=false")
        print("should_summarize=false")


if __name__ == "__main__":
    main()
