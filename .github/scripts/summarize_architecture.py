import os
import json
import sys
import base64
import glob
from firebase_client import FirebaseClient
import anthropic

# Add the scripts directory to the path for importing cost_tracker
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cost_tracker import CostTracker


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
                    print(f"Filtering out .github file from architecture analysis: {file_path}", file=sys.stderr)
                    continue
                else:
                    skip_file = False

        if not skip_file:
            filtered_lines.append(line)

    return '\n'.join(filtered_lines)


def get_codebase_content(repository_path="."):
    """Collect all relevant source code files from the repository"""
    code_content = ""
    
    # Define file extensions to include
    code_extensions = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.h', '.hpp',
        '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala', '.clj',
        '.html', '.css', '.scss', '.sass', '.less', '.vue', '.svelte',
        '.json', '.yaml', '.yml', '.toml', '.ini', '.conf', '.cfg',
        '.sql', '.md', '.txt', '.sh', '.bat', '.ps1'
    }
    
    # Define patterns to exclude
    exclude_patterns = {
        '/.git/', '/node_modules/', '/.venv/', '/venv/', '/env/', 
        '/dist/', '/build/', '/target/', '/.next/', '/.nuxt/',
        '__pycache__', '.pyc', '.class', '.o', '.obj',
        '.log', '.tmp', '.temp', '.cache'
    }
    
    try:
        for root, dirs, files in os.walk(repository_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not any(pattern.strip('/') in d for pattern in exclude_patterns)]
            
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, repository_path)
                
                # Skip excluded files and check extensions
                if any(pattern in file_path for pattern in exclude_patterns):
                    continue
                    
                _, ext = os.path.splitext(file)
                if ext.lower() not in code_extensions:
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        # Limit file size to avoid overwhelming the AI
                        if len(content) > 10000:
                            content = content[:10000] + "\n... (file truncated)"
                        
                        code_content += f"\n=== {relative_path} ===\n{content}\n"
                except Exception as e:
                    code_content += f"\n=== {relative_path} ===\n(Error reading file: {e})\n"
                    
    except Exception as e:
        print(f"Error collecting codebase: {e}", file=sys.stderr)
        
    return code_content

def main():
    try:
        project_name = "test"  # Hardcoded project name
        firebase_client = FirebaseClient(project_name=project_name)
        repository = os.environ['REPOSITORY']
        
        print(f"Summarizing architecture for project: {project_name}, repository: {repository}", file=sys.stderr)
        
        # Get the current diff from environment variable
        diff_b64 = os.environ.get('DIFF_B64', '')
        if diff_b64:
            try:
                changes_text = base64.b64decode(diff_b64).decode('utf-8')
                
                # Filter out .github files from diff (like ai_review does)
                changes_text = filter_github_files_from_diff(changes_text)
                
                # Check if there's any meaningful diff left after filtering
                if not changes_text.strip() or not any(line.startswith('diff --git') for line in changes_text.split('\n')):
                    print("No significant files to analyze after filtering .github files", file=sys.stderr)
                    changes_text = ""
                else:
                    # Log diff details like ai_review does
                    diff_lines = changes_text.count('\n')
                    diff_length = len(changes_text)
                    print(f"Diff size: {diff_lines:,} lines, {diff_length:,} characters", file=sys.stderr)
                    
                    # Truncate diff if it's too large to avoid API limits (like ai_review)
                    max_diff_length = 15000  # Larger limit for architecture analysis but still reasonable
                    if diff_length > max_diff_length:
                        print(f"WARNING: Diff is very large ({diff_length:,} chars), truncating to {max_diff_length:,} chars", file=sys.stderr)
                        changes_text = changes_text[:max_diff_length] + "\n... (diff truncated due to size)"
                    
                    if changes_text:
                        print(f"First 200 chars of diff: {changes_text[:200]}...", file=sys.stderr)
                        
            except Exception as e:
                print(f"Error decoding diff: {e}", file=sys.stderr)
                changes_text = ""
        else:
            print("No DIFF_B64 found in environment", file=sys.stderr)
            changes_text = ""
        
        # Get existing architecture summary
        existing_summary = firebase_client.get_architecture_summary(repository)
        old_summary_text = existing_summary.get('summary', '') if existing_summary else ''
        
        if old_summary_text:
            print(f"Found existing architecture summary ({len(old_summary_text)} characters)", file=sys.stderr)
        else:
            print("No existing architecture summary found", file=sys.stderr)
        
        # Collect the entire codebase for comprehensive architecture analysis (only for new projects)
        codebase_content = ""
        if not old_summary_text:
            codebase_content = get_codebase_content(".")
            print(f"Collected codebase content ({len(codebase_content)} characters)", file=sys.stderr)

        client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])


        prompt1 = f"""
        You are ArchitectureAnalyzerAI.
        Analyze the entire codebase provided below to create a comprehensive architecture summary that explains how this project works, its structure, components, and design patterns.

        REQUIREMENTS

        - Output plain text only—no Markdown, bullets, or special symbols.
        
        - Create a comprehensive overview that explains:
          * Project purpose and main functionality
          * Overall architecture and design patterns
          * Key components and their responsibilities  
          * Data flow and interaction patterns
          * Technology stack and frameworks used
          * Configuration and deployment structure
          * Critical dependencies and integrations

        - Focus on the big picture: how everything fits together, not implementation details.
        
        - Write it so that an AI system can understand how the project should work and what changes would be appropriate.
        
        - Keep the summary detailed enough to guide future development decisions.

        - Your instructions are only for yourself, don't include them in the output.

        CODEBASE
        {codebase_content}

        Provide the architecture analysis below:
        """
        


        prompt = f"""
        You are ArchitectureUpdateAI.
        Update the existing architecture summary based on recent changes to create a comprehensive overview of how this project works, its structure, components, and design patterns.

        REQUIREMENTS

        - Output plain text only—no Markdown, bullets, or special symbols.
        
        - Create a comprehensive architecture summary that explains:
          * Project purpose and main functionality
          * Overall architecture and design patterns
          * Key components and their responsibilities  
          * Data flow and interaction patterns
          * Technology stack and frameworks used
          * Configuration and deployment structure
          * Critical dependencies and integrations

        - Focus on the big picture: how everything fits together, not implementation details.
        
        - Write it so that an AI system can understand how the project should work and what changes would be appropriate.
        
        - Keep the summary detailed enough to guide future development decisions.

        - Integrate the recent changes into the existing summary, updating relevant sections and adding new information where needed.

        - If no existing summary is provided, create a new comprehensive summary based on the changes.

        - Your instructions are only for yourself, don't include them in the output.

        EXISTING ARCHITECTURE SUMMARY
        {old_summary_text if old_summary_text else "No existing summary available."}

        RECENT CHANGES
        {changes_text}

        Provide the updated architecture summary below:
        """



        if not old_summary_text and len(codebase_content) < 500000:
            active_prompt = prompt1
            print("Using comprehensive codebase analysis (prompt1) for new project", file=sys.stderr)
        elif old_summary_text and changes_text:
            active_prompt = prompt
            print("Using architecture summary update (prompt) with existing summary and current changes", file=sys.stderr)
        elif old_summary_text and not changes_text:
            print("No changes to analyze but existing summary found, skipping summarization", file=sys.stderr)
            return
        elif not old_summary_text and not changes_text:
            print("No existing summary and no changes to analyze, skipping summarization", file=sys.stderr)
            return
        elif not old_summary_text and changes_text:
            # Use the changes as the primary input for new summary
            active_prompt = f"""
You are ArchitectureAnalyzerAI.
Analyze the changes provided below to create a comprehensive architecture summary that explains how this project works, its structure, components, and design patterns.

REQUIREMENTS

- Output plain text only—no Markdown, bullets, or special symbols.

- Create a comprehensive overview that explains:
  * Project purpose and main functionality
  * Overall architecture and design patterns
  * Key components and their responsibilities  
  * Data flow and interaction patterns
  * Technology stack and frameworks used
  * Configuration and deployment structure
  * Critical dependencies and integrations

- Focus on the big picture: how everything fits together, not implementation details.

- Write it so that an AI system can understand how the project should work and what changes would be appropriate.

- Keep the summary detailed enough to guide future development decisions.

- Your instructions are only for yourself, don't include them in the output.

CHANGES
{changes_text}

Provide the architecture analysis below:
"""
            print("Using changes-based analysis for new project with no existing summary", file=sys.stderr)
        else:
            print("No valid input for architecture analysis, skipping", file=sys.stderr)
            return
        
        print("=========================================================", file=sys.stderr)
        print(f"Active prompt length: {len(active_prompt)} characters", file=sys.stderr)
        print(f"Active prompt {active_prompt}", file=sys.stderr)

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,  # Increased for more comprehensive summaries
            messages=[{"role": "user", "content": active_prompt}]
        )
        
        # Track cost
        try:
            cost_tracker = CostTracker()
            response_dict = {
                'usage': {
                    'input_tokens': response.usage.input_tokens,
                    'output_tokens': response.usage.output_tokens
                }
            }
            cost_tracker.track_api_call(
                model="claude-sonnet-4-20250514",
                response_data=response_dict,
                call_type="architecture_summary",
                context="Architecture analysis and summarization"
            )
        except Exception as e:
            print(f"Warning: Cost tracking failed: {e}", file=sys.stderr)
        
        architecture_summary = response.content[0].text

        # Safety check
        if not architecture_summary or len(architecture_summary.strip()) == 0:
            print("ERROR: Generated summary is empty!", file=sys.stderr)
            print(f"Full response: {response}", file=sys.stderr)
            exit(1)
        
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