#!/bin/bash

# Script to extract .github workflows from the Docker image
# Usage: ./extract-workflows.sh [destination-directory]

set -e

# Default destination directory
DEST_DIR="${1:-.github}"

echo "🚀 Extracting .github workflows from kaloyangavrilov/github-workflows:latest"
echo "📁 Destination: $DEST_DIR"

# Create temporary container
echo "📦 Creating temporary container..."
CONTAINER_ID=$(docker create kaloyangavrilov/github-workflows:latest)

# Copy .github folder
echo "📋 Copying .github folder..."
docker cp "$CONTAINER_ID:/app/.github" "$DEST_DIR"

# Create README for extracted workflows
echo "📝 Creating README for extracted workflows..."
cat > "$DEST_DIR/README.md" << 'EOF'
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
EOF

# Clean up container
echo "🧹 Cleaning up..."
docker rm "$CONTAINER_ID" > /dev/null

echo "✅ Successfully extracted .github workflows to: $DEST_DIR"
echo ""
echo "📖 Next steps:"
if [ "$DEST_DIR" = ".github" ]; then
    echo "1. You now have a .github folder ready to use in your repository"
    echo "2. Configure the required environment secrets:"
else
    echo "1. Copy the .github folder to your repository: cp -r $DEST_DIR/.github /path/to/your/repo/"
    echo "2. Configure the required environment secrets:"
fi
echo "   - FIREBASE_SERVICE_ACCOUNT_JSON"
echo "   - ANTHROPIC_API_KEY" 
echo "   - OPENAI_API_KEY"
echo "3. Customize the workflow files as needed for your project"
echo ""
echo "📚 For more information, see: https://hub.docker.com/r/kaloyangavrilov/github-workflows"
