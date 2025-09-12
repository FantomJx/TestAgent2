import json
import os
import sys
import subprocess
import base64
import re
from typing import List, Dict, Any


def clean_json_response(response_text: str) -> str:
    """Clean and extract JSON from AI response."""
    # Strip markdown code block formatting if present
    cleaned_text = response_text.replace(
        '```json', '').replace('```', '').strip()

    # Look for JSON array pattern
    json_match = re.search(r'\[.*\]', cleaned_text, re.DOTALL)
    if json_match:
        return json_match.group(0)
    else:
        return cleaned_text


def parse_review_comments(review_text: str) -> List[Dict[str, Any]]:
    """Parse review text and extract comments."""
    json_text = clean_json_response(review_text)

    try:
        comments = json.loads(json_text)
        if not isinstance(comments, list):
            print(
                f"Response is not a JSON array. Type: {type(comments)}", file=sys.stderr)
            return []

        return comments
    except json.JSONDecodeError as e:
        print(f"Invalid JSON response: {e}", file=sys.stderr)

        # Try to fix common JSON issues
        try:
            fixed_json = json_text.replace("'", '"')  # Replace single quotes
            # Add quotes to keys
            fixed_json = re.sub(r'(\w+):', r'"\1":', fixed_json)
            comments = json.loads(fixed_json)
            print("Successfully fixed JSON!", file=sys.stderr)
            return comments if isinstance(comments, list) else []
        except:
            print("Could not fix JSON", file=sys.stderr)
            return []


def add_diff_context_to_comment(comment_line: str, diff_content: str) -> str:
    """Add code context from diff to a failed comment line."""
    import re
    
    # Parse the comment line format: **path:line** - comment
    match = re.match(r'\*\*(.*?):(\d+)\*\* - (.*)', comment_line)
    if not match:
        return comment_line
    
    file_path, line_num, comment_text = match.groups()
    line_num = int(line_num)
    
    # Find the diff section for this file
    file_diff_pattern = rf"diff --git a/{re.escape(file_path)} b/{re.escape(file_path)}.*?(?=diff --git|\Z)"
    file_match = re.search(file_diff_pattern, diff_content, re.DOTALL)
    
    if not file_match:
        return comment_line
    
    file_diff = file_match.group(0)
    
    # Extract code context around the line number from the diff
    code_context = extract_code_context_from_diff(file_diff, line_num)
    
    if code_context:
        enhanced = f"**{file_path}:{line_num}** - {comment_text}\n\n```dart\n{code_context}\n```"
        return enhanced
    else:
        return comment_line


def extract_code_context_from_diff(file_diff: str, target_line: int) -> str:
    """Extract code context around a specific line from a diff."""
    lines = file_diff.split('\n')
    context_lines = []
    current_new_line = 0
    in_hunk = False
    
    for line in lines:
        if line.startswith('@@'):
            # Parse hunk header: @@ -old_start,old_count +new_start,new_count @@
            hunk_match = re.match(r'@@ -\d+,?\d* \+(\d+),?\d* @@', line)
            if hunk_match:
                current_new_line = int(hunk_match.group(1)) - 1
                in_hunk = True
                continue
        
        if not in_hunk:
            continue
            
        if line.startswith(' '):
            # Unchanged line
            current_new_line += 1
            if abs(current_new_line - target_line) <= 3:
                context_lines.append(f"  {current_new_line:3d} | {line[1:]}")
        elif line.startswith('+'):
            # Added line
            current_new_line += 1
            if abs(current_new_line - target_line) <= 3:
                prefix = "→" if current_new_line == target_line else " "
                context_lines.append(f"{prefix} {current_new_line:3d} | {line[1:]}")
        elif line.startswith('-'):
            # Removed line - don't increment new line counter but show for context
            if abs(current_new_line - target_line) <= 3:
                context_lines.append(f"  --- | {line[1:]}")
    
    # Filter context lines to show only around target line
    if not context_lines:
        return ""
    
    # Find the target line and get context around it
    target_context = []
    for i, context_line in enumerate(context_lines):
        if f"→ {target_line:3d}" in context_line:
            # Found target line, get context
            start = max(0, i - 2)
            end = min(len(context_lines), i + 3)
            target_context = context_lines[start:end]
            break
    
    return '\n'.join(target_context) if target_context else '\n'.join(context_lines[:5])


def post_summary_comment(github_token: str, github_repo: str, pr_number: str,
                         comments: list, model_comment: str) -> bool:
    """Post a summary comment to GitHub PR with all review content."""
    # Count actual valid comments with all required fields
    valid_issue_count = 0
    for comment_obj in comments:
        if (isinstance(comment_obj, dict) and 
            comment_obj.get('path') and 
            comment_obj.get('line') and 
            comment_obj.get('comment')):
            valid_issue_count += 1
    
    if valid_issue_count == 0:
        summary_text = f"✅ Code review completed - no issues found! {model_comment}"
    else:
        summary_text = f"🤖 **AI Code Review** - Found {valid_issue_count} issues that need attention.\n\n{model_comment}\n\n"
        summary_text += "### 📝 Code Review Issues\n"
        summary_text += "*(Issues found in your code with context - processed using smart chunking for thorough analysis)*\n\n"
        
        # Read the diff to extract code context
        diff_content = ""
        diff_file_path = os.environ.get('DIFF_FILE_PATH', '/tmp/pr_diff.txt')
        if os.path.exists(diff_file_path):
            with open(diff_file_path, 'r', encoding='utf-8') as f:
                diff_content = f.read()
        
        # Add all comments with enhanced context
        for comment_obj in comments:
            if not isinstance(comment_obj, dict):
                continue
                
            path = comment_obj.get('path', '')
            line = comment_obj.get('line', 0)
            comment = comment_obj.get('comment', '')
            
            if not all([path, line, comment]):
                continue
                
            # Create comment line in the expected format
            comment_line = f"**{path}:{line}** - {comment}"
            enhanced_comment = add_diff_context_to_comment(comment_line, diff_content)
            summary_text += f"{enhanced_comment}\n\n"

    summary_comment = {"body": summary_text}
    with open('/tmp/summary_comment.json', 'w') as f:
        json.dump(summary_comment, f)

    result = subprocess.run([
        'curl', '-s', '-X', 'POST',
        '-H', f'Authorization: Bearer {github_token}',
        '-H', 'Content-Type: application/json',
        '--data', '@/tmp/summary_comment.json',
        f'https://api.github.com/repos/{github_repo}/issues/{pr_number}/comments'
    ], capture_output=True, text=True)

    return result.returncode == 0


def process_and_post_comments():
    """Main function to process AI review and post comments."""
    # Get environment variables
    review_b64 = os.environ.get('REVIEW_TEXT', '')
    model_comment = os.environ.get('MODEL_COMMENT', '')
    github_token = os.environ.get('GITHUB_TOKEN', '')
    github_repo = os.environ.get('GITHUB_REPOSITORY', '')
    pr_number = os.environ.get('PR_NUMBER', '')
    head_sha = os.environ.get('HEAD_SHA', '')

    if not all([review_b64, github_token, github_repo, pr_number, head_sha]):
        print("Missing required environment variables", file=sys.stderr)
        sys.exit(1)

    print(f"Processing review for PR #{pr_number}")

    # Decode the review text
    try:
        review_text = base64.b64decode(review_b64).decode('utf-8')
    except Exception as e:
        print(f"Failed to decode review text: {e}", file=sys.stderr)
        sys.exit(1)

    # Parse comments
    print(f"Raw review text preview: {review_text[:200]}...", file=sys.stderr)
    comments = parse_review_comments(review_text)
    print(f"Found {len(comments)} review comments to include in summary")
    
    if len(comments) == 0:
        print("No issues found in the code review - this is good!")

    # Filter valid comments for summary
    valid_comments = []
    for comment_obj in comments:
        if not isinstance(comment_obj, dict):
            continue

        path = comment_obj.get('path')
        line = comment_obj.get('line')
        comment = comment_obj.get('comment')

        # Skip if any field is missing or invalid
        if not all([path, line, comment]) or not isinstance(line, int):
            print(f"Skipping invalid comment: {comment_obj}", file=sys.stderr)
            continue

        # Skip formatting-related comments
        comment_lower = comment.lower()
        skip_patterns = [
            'missing newline at end of file',
            'newline at end of file',
            'trailing whitespace',
            'missing final newline',
            'add newline at end',
            'file should end with newline',
            'no newline at end of file'
        ]
        
        if any(pattern in comment_lower for pattern in skip_patterns):
            print(f"Skipping formatting comment: {comment}", file=sys.stderr)
            continue

        valid_comments.append(comment_obj)

    print(f"Posting summary comment with {len(valid_comments)} review issues")

    # Post only summary comment with all review content
    print(f"Final valid comments count: {len(valid_comments)}")
    if post_summary_comment(github_token, github_repo, pr_number, valid_comments, model_comment):
        print("Summary comment posted successfully")
    else:
        print("Failed to post summary comment", file=sys.stderr)


if __name__ == "__main__":
    process_and_post_comments()
