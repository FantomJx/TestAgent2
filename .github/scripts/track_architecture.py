import json
import os
import sys
import subprocess
import base64
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple


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


def generate_architecture_summary(summary_text: str, file_paths: List[str], pr_number: str) -> str:
    """Generate a formatted summary for the architecture file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    summary = f"\n--- PR #{pr_number} - {timestamp} ---\n"
    summary += f"Files modified: {', '.join(file_paths)}\n"
    summary += f"Changes: {summary_text}\n"
    
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
                    print(f"Filtering out .github file: {file_path}", file=sys.stderr)
                    continue
                else:
                    skip_file = False
        
        if not skip_file:
            filtered_lines.append(line)
    
    return '\n'.join(filtered_lines)


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
        
        # Filter out .github files from the diff
        diff = filter_github_files_from_diff(diff)
        
        # Check if there's any meaningful diff left after filtering
        if not diff.strip() or not any(line.startswith('diff --git') for line in diff.split('\n')):
            print("No significant files to analyze after filtering .github files", file=sys.stderr)
            print("arch_updated=false")
            word_count = get_word_count("architecture_summary.txt")
            if word_count > 1000:
                print("should_summarize=true")
            else:
                print("should_summarize=false")
            return
        
        # Track all changes without significance analysis
        file_paths = get_file_paths_from_diff(diff)
        
        # Generate basic summary of changes
        basic_summary = f"Modified {len(file_paths)} files: {', '.join(file_paths[:5])}"
        if len(file_paths) > 5:
            basic_summary += f" and {len(file_paths) - 5} more files"
        
        summary = generate_architecture_summary(basic_summary, file_paths, pr_number)
        append_to_architecture_file(summary)
        print(f"Architecture summary updated: {basic_summary}", file=sys.stderr)
        print("arch_updated=true")
        
        # Check if summarization is needed
        word_count = get_word_count("architecture_summary.txt")
        print(f"Architecture file word count: {word_count}", file=sys.stderr)
        
        if word_count > 400:
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