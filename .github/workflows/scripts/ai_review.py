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

            # Raise exception for retryable errors
            if error_type in ['overloaded_error', 'rate_limit_error']:
                raise Exception(f"Claude API {error_type}: {error_message}")

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


def create_review_prompt(diff: str, chunk_num: int = None, total_chunks: int = None) -> str:
    """Create the review prompt for the AI model."""
    architecture_context = read_architecture_context()

    # Get custom AI prompt from environment
    custom_ai_prompt = os.environ.get('CUSTOM_AI_PROMPT', '').strip()

    # Log minimal diff details
    diff_lines = diff.count('\n')
    diff_length = len(diff)
    
    if chunk_num and total_chunks:
        print(f"Chunk {chunk_num}/{total_chunks} - Diff size: {diff_lines:,} lines, {diff_length:,} characters", file=sys.stderr)
    else:
        print(f"Diff size: {diff_lines:,} lines, {diff_length:,} characters", file=sys.stderr)

    if custom_ai_prompt:
        print(
            f"Using custom AI prompt: {custom_ai_prompt[:100]}{'...' if len(custom_ai_prompt) > 100 else ''}", file=sys.stderr)

    # With smart chunking, we no longer need truncation as chunks are appropriately sized

    # Build the base prompt
    chunk_context = ""
    if chunk_num and total_chunks and total_chunks > 1:
        chunk_context = f"""
    
    CHUNK CONTEXT
    This is chunk {chunk_num} of {total_chunks} from a larger diff. Focus on reviewing the files in this chunk thoroughly, as each chunk will be reviewed independently."""

    base_prompt = f"""You are a helpful and diligent code assistant. Review the following unified diff and provide line-by-line feedback for specific issues.

    TASK
    Review the unified diff below and return feedback **only** on lines that were *added* or *modified*.{chunk_context}

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
    7. Skip minor formatting issues like "Missing newline at end of file", trailing whitespace, or similar linting issues.
    8. GROUP SIMILAR ISSUES: If you find multiple instances of the same type of issue (e.g., hardcoded strings, missing localization, commented code), create ONE comment that lists all affected locations instead of separate comments for each instance.
       Example: Instead of 3 separate comments for hardcoded strings, create one comment like:
       "Hardcoded strings found - use localization: lines 25, 47, 89"

    DIFF TO REVIEW
    ```diff
    {diff}
```"""

    return base_prompt





def get_ai_review_for_chunk(model: str, chunk: str, chunk_num: int, total_chunks: int) -> str:
    """Get AI review for a single diff chunk."""
    prompt = create_review_prompt(chunk, chunk_num, total_chunks)
    
    api_key = os.environ.get('ANTHROPIC_API_KEY', '')
    if not api_key:
        print('ANTHROPIC_API_KEY not found', file=sys.stderr)
        return '[]'

    payload = create_claude_payload(model, prompt)
    return call_claude_api(api_key, payload)


def merge_review_results(results: list) -> str:
    """Merge multiple JSON review results into a single JSON array."""
    import json
    import re
    
    all_comments = []
    
    for result in results:
        if not result or result.strip() == '[]':
            continue
            
        try:
            # Parse the JSON result
            result_clean = result.replace('```json', '').replace('```', '').strip()
            # Look for JSON array pattern
            json_match = re.search(r'\[.*\]', result_clean, re.DOTALL)
            if json_match:
                result_clean = json_match.group(0)
            
            comments = json.loads(result_clean)
            if isinstance(comments, list):
                all_comments.extend(comments)
        except json.JSONDecodeError as e:
            print(f"Failed to parse review result: {e}", file=sys.stderr)
            print(f"Result was: {result[:200]}...", file=sys.stderr)
            continue
    
    return json.dumps(all_comments)


def get_ai_review(model: str, diff: str) -> str:
    """Get AI review for the given diff using Claude model with smart chunking."""
    # Filter out GitHub workflow files and binary files first
    print(f"Diff size before filtering: {len(diff)} bytes", file=sys.stderr)
    filtered_diff = filter_github_files_from_diff(diff)
    print(f"Diff size after filtering: {len(filtered_diff)} bytes", file=sys.stderr)
    
    # Count files in filtered diff
    file_count = filtered_diff.count('diff --git')
    print(f"Files in diff after filtering: {file_count}", file=sys.stderr)
    
    # Check if we need chunking - be more conservative due to token limits
    max_single_chunk_size = 50000  # 500KB - back to working size
    
    if len(filtered_diff) <= max_single_chunk_size:
        # Small diff - process as single chunk with retry logic
        print("Processing diff as single chunk", file=sys.stderr)
        prompt = create_review_prompt(filtered_diff)
        
        api_key = os.environ.get('ANTHROPIC_API_KEY', '')
        if not api_key:
            print('ANTHROPIC_API_KEY not found', file=sys.stderr)
            return '[]'

    
        payload = create_claude_payload(model, prompt)
        return call_claude_api(api_key, payload)
    
    else:
        # Large diff - use smart chunking
        print(f"Large diff ({len(filtered_diff):,} chars) - using smart chunking", file=sys.stderr)
        chunks = split_diff_intelligently(filtered_diff, max_chunk_size=50000)  # 150KB per chunk - smaller to avoid overload errors
        
        if len(chunks) == 1:
            # Only one chunk after splitting - process normally
            print("Only one chunk after splitting", file=sys.stderr)
            prompt = create_review_prompt(chunks[0])
            
            api_key = os.environ.get('ANTHROPIC_API_KEY', '')
            if not api_key:
                print('ANTHROPIC_API_KEY not found', file=sys.stderr)
                return '[]'

            payload = create_claude_payload(model, prompt)
            return call_claude_api(api_key, payload)
        else:
            # Multiple chunks - process each and merge
            print(f"Processing {len(chunks)} chunks", file=sys.stderr)
            results = []
            
            for i, chunk in enumerate(chunks):
                # Add delay between API calls to respect rate limits
                # 30K tokens/minute limit means we need ~2 minute spacing for large chunks
                import time
                if i > 0:  # Don't delay before the first chunk
                    delay = 60   # 1 minute to respect rate limits - balance speed vs limits
                    print(f"Waiting {delay} seconds to respect rate limits...", file=sys.stderr)
                    time.sleep(delay)
                
                print(f"Processing chunk {i+1}/{len(chunks)} ({len(chunk):,} chars)", file=sys.stderr)
                
                # Try to get review for this chunk with retry on rate limit
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        result = get_ai_review_for_chunk(model, chunk, i+1, len(chunks))
                        print(f"Chunk {i+1} result length: {len(result)} chars", file=sys.stderr)
                        
                        # Check if result is just empty array
                        if result.strip() in ['[]', '[ ]', '[\n]']:
                            print(f"WARNING: Chunk {i+1} returned empty array - no issues found", file=sys.stderr)
                        
                        results.append(result)
                        break
                    except Exception as e:
                        error_str = str(e).lower()
                        if ("rate_limit" in error_str or "overloaded" in error_str) and attempt < max_retries - 1:
                            # Exponential backoff for overloaded/rate limit errors
                            retry_delay = 120 * (2 ** attempt)  # 2 min, 4 min, 8 min
                            print(f"API overloaded/rate limited, waiting {retry_delay} seconds before retry {attempt + 1}/{max_retries}...", file=sys.stderr)
                            time.sleep(retry_delay)
                        else:
                            print(f"Failed to process chunk {i+1} after {attempt + 1} attempts: {e}", file=sys.stderr)
                            results.append('[]')  # Add empty result to maintain chunk order
                            break
            
            # Merge all results
            merged_result = merge_review_results(results)
            print(f"Merged results from {len(chunks)} chunks", file=sys.stderr)
            return merged_result


def parse_diff_by_file(diff: str) -> list:
    """Parse unified diff into individual file diffs."""
    if not diff.strip():
        return []
    
    files = []
    current_file = []
    
    lines = diff.split('\n')
    for line in lines:
        if line.startswith('diff --git'):
            # Start of a new file - save previous file if exists
            if current_file:
                files.append('\n'.join(current_file))
            current_file = [line]
        else:
            current_file.append(line)
    
    # Add the last file
    if current_file:
        files.append('\n'.join(current_file))
    
    return files


def split_diff_intelligently(diff: str, max_chunk_size: int = 50000) -> list:
    """Split diff by files, grouping small files and splitting large ones."""
    files = parse_diff_by_file(diff)
    if not files:
        return [diff]
    
    chunks = []
    current_chunk = []
    current_size = 0
    
    for file_diff in files:
        file_size = len(file_diff)
        
        if file_size > max_chunk_size:
            # Large file - process separately
            if current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
                current_size = 0
            chunks.append(file_diff)
            print(f"Large file separated into its own chunk: {file_size:,} chars", file=sys.stderr)
        elif current_size + file_size > max_chunk_size:
            # Would exceed chunk size - start new chunk
            if current_chunk:
                chunks.append('\n'.join(current_chunk))
            current_chunk = [file_diff]
            current_size = file_size
        else:
            # Add to current chunk
            current_chunk.append(file_diff)
            current_size += file_size
    
    # Add the last chunk if it has content
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    
    print(f"Split diff into {len(chunks)} chunks", file=sys.stderr)
    for i, chunk in enumerate(chunks):
        # Count files in this chunk
        file_count = chunk.count('diff --git')
        print(f"Chunk {i+1}: {len(chunk):,} chars, {file_count} files", file=sys.stderr)
    
    return chunks


def filter_github_files_from_diff(diff: str) -> str:
    """Filter diff to focus on source code files that are worth reviewing."""
    lines = diff.split('\n')
    filtered_lines = []
    skip_file = False

    # Files to INCLUDE (source code that should be reviewed)
    include_patterns = [
        '.dart',           # Dart source files
        '.java',           # Java files  
        '.kt', '.kts',     # Kotlin files
        '.swift',          # Swift files
        '.js', '.ts',      # JavaScript/TypeScript
        '.py',             # Python files
        '.cpp', '.cc', '.cxx', '.c', '.h', '.hpp',  # C/C++ files
        '.rs',             # Rust files
        '.go',             # Go files
        '.rb',             # Ruby files
        '.php',            # PHP files
        '.cs',             # C# files
        '.scala',          # Scala files
        '.m',              # Objective-C files
        'CMakeLists.txt',  # CMake files
        'Podfile',
        '.sql'         # iOS dependency files
    ]
    
    # Files to EXCLUDE (even if they match include patterns)
    exclude_patterns = [
        '.gradle',   
        '.github/',                    # GitHub workflows
        '.dart_tool/',                # Dart build cache
        'build/',                     # Build outputs
        '.generated.dart',            # Generated Dart files
        '.freezed.dart',              # Freezed generated files
        '.g.dart',                    # Code generation files
        '.mocks.dart',                # Mock files
        'firebase_options.dart',      # Firebase config
        'google-services.json',       # Google services config
        '.lock',                      # Lock files
        '.pbxproj',                   # Xcode project files
        '.plist',                     # Property list files
        'package_config.json',        # Dart package config
        'package_graph.json',         # Dart package graph
        '.arb',                       # Localization files
        'analysis_options.yaml',      # Dart analysis config
        'pubspec.yaml',               # Dart package config
        'pubspec.lock',               # Dart lock file
        '/test/',                     # Test files (usually clean)
        '_test.dart',                 # Test files
        '.test.dart',                 # Test files
        'android/app/src/main/res/',  # Android resources
        'android/app/src/dev/res/',   # Android dev resources  
        'android/app/src/prod/res/',  # Android prod resources
        'ios/Runner/Assets.xcassets/',# iOS assets
        'web/splash/',                # Web splash assets
        'assets/',                    # Asset files
        '.xcassets/',                 # iOS asset catalogs
        'launch_background.xml',      # Android launch backgrounds
        'styles.xml',                 # Android styles
        '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg',  # Images
        '.ttf', '.otf', '.woff', '.woff2',                # Fonts
        '.zip', '.tar', '.gz', '.bz2',                    # Archives
        '.pdf', '.doc', '.docx',                          # Documents
        '.mp4', '.avi', '.mov', '.mp3', '.wav',            # Media
        '.md'              # Documentation files

    ]

    for line in lines:
        if line.startswith('diff --git'):
            # Extract file path
            parts = line.split()
            if len(parts) >= 4:
                file_path = parts[3][2:]  # Remove "b/" prefix
                
                # First check if it should be excluded
                should_exclude = any(pattern in file_path.lower() for pattern in exclude_patterns)
                
                if should_exclude:
                    skip_file = True
                    continue
                
                # Then check if it's a source code file we want to include
                should_include = any(file_path.lower().endswith(pattern.lower()) or pattern in file_path.lower() 
                                   for pattern in include_patterns)
                
                if should_include:
                    skip_file = False
                else:
                    skip_file = True
                    continue

        if not skip_file:
            filtered_lines.append(line)

    return '\n'.join(filtered_lines)


if __name__ == "__main__":
    # Get environment variables
    diff_file_path = os.environ.get('DIFF_FILE_PATH', '')
    is_summary_only = os.environ.get('IS_SUMMARY_ONLY', 'false').lower() == 'true'
    model = os.environ.get('MODEL', '')
    has_important_label = os.environ.get(
        'HAS_IMPORTANT_LABEL', 'false').lower() == 'true'
    if not diff_file_path:
        print('Missing required environment variable: DIFF_FILE_PATH', file=sys.stderr)
        sys.exit(1)

    # Read diff from file
    try:
        with open(diff_file_path, 'r', encoding='utf-8') as f:
            diff = f.read()
    except FileNotFoundError:
        print(f'Diff file not found: {diff_file_path}', file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f'Error reading diff file: {e}', file=sys.stderr)
        sys.exit(1)

    # Filter out .github files from diff
    original_diff_size = len(diff)
    diff = filter_github_files_from_diff(diff)
    filtered_diff_size = len(diff)
    
    print(f"Diff size before filtering: {original_diff_size} bytes", file=sys.stderr)
    print(f"Diff size after filtering: {filtered_diff_size} bytes", file=sys.stderr)
    
    # Count diff --git lines to see how many files remain
    diff_files = [line for line in diff.split('\n') if line.startswith('diff --git')]
    print(f"Files in diff after filtering: {len(diff_files)}", file=sys.stderr)
    
    # Files are now filtered and ready for processing

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
