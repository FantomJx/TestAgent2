# GitHub Workflows Docker Image

This Docker image packages GitHub workflows for AI-powered code review and architecture analysis.

## Features

- AI code review using Claude Sonnet 4 and GPT-4.1 Nano
- Architecture summary generation
- Firebase integration for configuration management
- Cost tracking for AI API usage
- Configurable thresholds and settings

## Usage

### Pull the image
```bash
docker pull kaloyangavrilov/github-workflows:latest
```

### Run health check
```bash
docker run --rm kaloyangavrilov/github-workflows:latest health
```

### Fetch configuration macros
```bash
docker run --rm \
  -e FIREBASE_SERVICE_ACCOUNT_JSON="$FIREBASE_JSON" \
  kaloyangavrilov/github-workflows:latest fetch-macros
```

### Run AI code review
```bash
docker run --rm \
  -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  kaloyangavrilov/github-workflows:latest ai-review "$(cat diff.txt)"
```

### Interactive shell
```bash
docker run -it --rm kaloyangavrilov/github-workflows:latest bash
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Firebase service account JSON | Yes |
| `ANTHROPIC_API_KEY` | Anthropic API key | Yes |
| `OPENAI_API_KEY` | OpenAI API key | Yes |
| `LINE_THRESHOLD` | Line threshold for model selection | No (default: 200) |
| `CHANGES_THRESHOLD` | Changes threshold for architecture updates | No (default: 5) |

## Docker Compose

```yaml
version: '3.8'
services:
  github-workflows:
    image: kaloyangavrilov/github-workflows:latest
    environment:
      - FIREBASE_SERVICE_ACCOUNT_JSON=${FIREBASE_SERVICE_ACCOUNT_JSON}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    command: health
```

## Building Locally

```bash
docker build -t github-workflows:local .
docker run --rm github-workflows:local health
```

## Tags

- `latest` - Latest stable version
- `main` - Latest development version
- `v1.0.0` - Specific version tags

## Extracting Workflows for Other Repositories

You can extract the `.github` workflows from this Docker image to use in other repositories:

### Method 1: Using the extraction script
```bash
# Download the extraction script
curl -O https://raw.githubusercontent.com/yourusername/yourrepo/main/extract-workflows.sh
chmod +x extract-workflows.sh

# Extract workflows to a directory
./extract-workflows.sh .github

# Now you have .github folder ready to use in your repository
```

### Method 2: Manual extraction
```bash
# Create temporary container
docker create --name temp-extract kaloyangavrilov/github-workflows:latest

# Copy .github folder
docker cp temp-extract:/app/.github ./.github

# Clean up
docker rm temp-extract

# Now you have .github folder ready to use
```

### What you get:
- AI-powered code review workflows
- Architecture summary generation
- Cost tracking for AI API usage
- Firebase integration scripts
- Pull request templates

### Required setup in your new repository:
1. Add the following secrets to your repository:
   - `FIREBASE_SERVICE_ACCOUNT_JSON`
   - `ANTHROPIC_API_KEY`
   - `OPENAI_API_KEY`
2. Customize workflow triggers and settings as needed
3. Update Firebase configuration for your project
