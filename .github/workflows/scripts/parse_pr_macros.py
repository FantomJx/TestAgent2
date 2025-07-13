import os
import re
import sys

def parse_pr_description_macros(pr_body):
    """Parse macro configuration from PR description."""
    macros = {}
    
    if not pr_body:
        return macros
    
    # Define patterns to match the simplified format
    patterns = {
        'LINE_THRESHOLD': r'\*\* Use Claude when PR has more than:\*\*\s*`([^`]+)`',
        'CHANGES_THRESHOLD': r'\*\* Update architecture summary when:\*\*\s*`([^`]+)`'
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, pr_body, re.IGNORECASE | re.MULTILINE)
        if match:
            value = match.group(1).strip()
            # Extract just the number if it has text like "200 lines" or "5 or more files"
            number_match = re.search(r'(\d+)', value)
            if number_match:
                numeric_value = number_match.group(1)
                # Only use if it's different from defaults
                if (key == 'LINE_THRESHOLD' and numeric_value != '200') or \
                   (key == 'CHANGES_THRESHOLD' and numeric_value != '1'):
                    macros[key] = numeric_value
    
    # Parse custom prompt additions
    # Look for a pattern like: ** Custom AI Review Instructions: ** `custom text here`
    custom_prompt_pattern = r'\*\*\s*Custom AI Review Instructions:\s*\*\*\s*`([^`]+)`'
    custom_match = re.search(custom_prompt_pattern, pr_body, re.IGNORECASE | re.MULTILINE)
    if custom_match:
        custom_prompt = custom_match.group(1).strip()
        if custom_prompt:
            macros['CUSTOM_PROMPT_ADDITIONS'] = custom_prompt
    
    return macros

def main():
    """Main function to parse PR description macros and set GitHub outputs."""
    pr_body = os.environ.get('PR_BODY', '')
    
    # Parse macros from PR description
    pr_macros = parse_pr_description_macros(pr_body)
    
    # Set GitHub Actions outputs for found macros
    output_file = os.environ.get('GITHUB_OUTPUT', '/dev/stdout')
    with open(output_file, 'a') as f:
        for key, value in pr_macros.items():
            f.write(f"pr_{key.lower()}={value}\n")
    
    # Also output whether we found any macros in the PR description
    has_pr_macros = len(pr_macros) > 0
    with open(output_file, 'a') as f:
        f.write(f"has_pr_macros={str(has_pr_macros).lower()}\n")

if __name__ == "__main__":
    main()
