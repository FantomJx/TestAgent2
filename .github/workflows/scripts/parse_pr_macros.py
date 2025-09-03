import os
import re
import sys


def parse_pr_description_macros(pr_body):
    """Parse macro configuration from PR description."""
    macros = {}

    if not pr_body:
        return macros

    # Parse custom AI prompt instructions
    custom_prompt_pattern = r'\*\* Additional prompt instructions:\*\*\s*```\s*(.*?)\s*```'
    custom_prompt_match = re.search(
        custom_prompt_pattern, pr_body, re.IGNORECASE | re.MULTILINE | re.DOTALL)
    if custom_prompt_match:
        custom_prompt = custom_prompt_match.group(1).strip()
        # Remove HTML comments and empty lines
        custom_prompt = re.sub(
            r'<!--.*?-->', '', custom_prompt, flags=re.DOTALL)
        custom_prompt = '\n'.join(
            line.strip() for line in custom_prompt.split('\n') if line.strip())
        if custom_prompt:
            macros['CUSTOM_AI_PROMPT'] = custom_prompt

    # Check for "Update architecture summary" checkbox marked with X
    if re.search(r'\[X\].*[Uu]pdate architecture summary', pr_body, re.IGNORECASE | re.MULTILINE):
        macros['UPDATE_ARCHITECTURE_SUMMARY'] = 'true'

    return macros


def main():
    """Main function to parse PR description macros and set GitHub outputs."""
    pr_body = os.environ.get('PR_BODY', '')

    # Parse macros from PR description
    pr_macros = parse_pr_description_macros(pr_body)

    # Set GitHub Actions outputs for found macros (strip any carriage returns)
    output_file = os.environ.get('GITHUB_OUTPUT', '/dev/stdout')
    with open(output_file, 'a') as f:
        for key, value in pr_macros.items():
            clean_value = str(value).replace('\r', '').replace('\n', ' ')
            f.write(f"pr_{key.lower()}={clean_value}\n")

    # Also output whether we found any macros in the PR description
    has_pr_macros = len(pr_macros) > 0
    with open(output_file, 'a') as f:
        f.write(f"has_pr_macros={str(has_pr_macros).lower()}\n")


if __name__ == "__main__":
    main()
