# Extracted GitHub Workflows

This directory contains GitHub workflows and Python scripts extracted from the `kaloyangavrilov/github-workflows` Docker image.

## Contents

- **workflows/**: GitHub Actions workflow files and Python scripts
- **pull_request_template.md**: Pull request template

## Setup Instructions

1. **Copy to your repository**:
   ```bash
   cp -r .github /path/to/your/repository/
   ```

2. **Add repository secrets**:
   Go to your repository → Settings → Secrets and variables → Actions, and add:
   - `FIREBASE_SERVICE_ACCOUNT_JSON` - Firebase service account JSON
   - `ANTHROPIC_API_KEY` - Anthropic API key for Claude
   - `OPENAI_API_KEY` - OpenAI API key for GPT models

3. **Install dependencies** (if running scripts locally):
   ```bash
   pip install firebase-admin anthropic openai
   ```

## Available Workflows

- **AI Code Review**: Automated code review using Claude and GPT models
- **Architecture Summary**: Generate architecture summaries for large changes
- **Cost Tracking**: Track AI API usage and costs
- **Firebase Integration**: Fetch and manage configuration from Firebase

## Customization

You may need to customize the workflow files for your specific project:

1. Update trigger conditions in `.yml` files
2. Modify thresholds and settings in Python scripts
3. Update Firebase project configuration
4. Adjust model selection logic based on your needs

## Source

These workflows were extracted from: https://hub.docker.com/r/kaloyangavrilov/github-workflows

For updates and documentation, visit the original Docker image repository.
