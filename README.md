# AI Code Review System

A comprehensive GitHub Actions workflow that provides automated code review using AI models (Claude 4 Sonnet and GPT o3-mini) with intelligent model selection, architecture change tracking, and automatic summarization.

## Overview

This system automatically reviews pull requests using AI models and provides:
- Line-by-line code review comments
- Intelligent model selection based on PR characteristics
- Architecture change tracking for important changes
- Automatic summarization of architecture documentation
- Support for both Claude and OpenAI APIs

## Architecture

The system consists of four main components:

### 1. GitHub Actions Workflow (`.github/workflows/blank.yml`)
- Triggers on pull request events (opened, synchronize, reopened)
- Orchestrates the entire review process
- Handles Git operations and conflict resolution

### 2. AI Review Engine (`.github/scripts/ai_review.py`)
- Performs the actual code review using AI models
- Implements intelligent model selection logic
- Filters out workflow files from review
- Handles API communication with Claude and OpenAI

### 3. Architecture Tracker (`.github/scripts/track_architecture.py`)
- Tracks significant architectural changes
- Maintains a running log of modifications
- Triggers summarization when needed

### 4. Comment Poster (`.github/scripts/post_comments.py`)
- Posts line-by-line comments to GitHub PRs
- Handles JSON parsing and error recovery
- Posts summary comments with review statistics

## Setup Instructions

### Step 1: Repository Secrets Configuration

Configure the following secrets in your GitHub repository (Settings > Secrets and variables > Actions):

#### Required Secrets:
- `ANTHROPIC_API_KEY`: Your Anthropic API key for Claude access
- `OPENAI_API_KEY`: Your OpenAI API key for GPT access
- `PAT_TOKEN`: Personal Access Token with the following permissions:
  - `repo` (full repository access)
  - `pull_requests` (read and write)
  - `contents` (read and write)

#### PAT Token Setup:
1. Go to GitHub Settings > Developer settings > Personal access tokens
2. Generate a new token (classic) with the required permissions
3. Add it as `PAT_TOKEN` in your repository secrets

### Step 2: Workflow File Setup

1. Create the `.github/workflows/` directory structure in your repository
2. Copy the workflow file to `.github/workflows/blank.yml`
3. Copy all Python scripts to `.github/scripts/` directory:
   - `ai_review.py`
   - `track_architecture.py`
   - `summarize_architecture.py`
   - `post_comments.py`

### Step 3: Configuration Variables

The workflow uses the following configurable environment variables:

- `LINE_THRESHOLD`: Number of changed lines that triggers Claude usage (default: 0)
- Set this in the workflow file's `env` section

## Usage

### Basic Code Review

The system automatically reviews all pull requests. No special configuration required.

### Architecture Change Tracking

To enable architecture tracking for important changes:

1. Add `#IMPORTANT-CHANGE` to your pull request title
2. The system will automatically track the changes in `architecture_summary.txt`
3. When the file grows large, it will be automatically summarized

### Model Selection Logic

The system intelligently selects between AI models:

**Claude 4 Sonnet is used when:**
- PR has "important changes" label
- Changed lines exceed the `LINE_THRESHOLD`
- PR title contains `#IMPORTANT-CHANGE`

**GPT o3-mini is used for:**
- Small PRs under the threshold
- Regular maintenance changes

### Labels

Add the following labels to your repository for enhanced functionality:
- `important changes`: Forces Claude usage regardless of PR size

## Features

### Intelligent Review
- Considers architectural context from previous changes
- Focuses only on added/modified lines
- Provides actionable, specific feedback
- Avoids reviewing workflow files

### Architecture Tracking
- Maintains a log of significant changes
- Automatically summarizes when the log grows large
- Creates timestamped backups before summarization
- Tracks file modifications and PR metadata

### Error Handling
- Graceful handling of API failures
- Git conflict resolution
- JSON parsing with error recovery
- Extensive logging for debugging

### Performance Optimization
- Filters out non-essential files from review
- Truncates large diffs to avoid API limits
- Implements payload size warnings
- Optimized for token usage

## File Structure

```
.github/
├── workflows/
│   └── blank.yml                 # Main workflow file
└── scripts/
    ├── ai_review.py             # AI review engine
    ├── track_architecture.py    # Architecture change tracker
    ├── summarize_architecture.py # Architecture summarizer
    └── post_comments.py         # Comment posting system
architecture_summary.txt          # Architecture change log
```

## Troubleshooting

### Common Issues

**API Key Errors:**
- Verify all required secrets are set correctly
- Check API key permissions and quotas
- Ensure keys are active and not expired

**Permission Errors:**
- Verify PAT token has required permissions
- Check repository permissions for the token
- Ensure the token belongs to a user with appropriate access

**No Comments Posted:**
- Check if the AI found any issues (empty array is valid)
- Verify the diff contains meaningful changes
- Check GitHub API rate limits

### Debug Information

The system provides extensive logging:
- Payload sizes and content details
- API call status and responses
- File filtering information
- Model selection reasoning

Check the workflow logs for detailed debugging information.

## Workflow Steps Explained

1. **Checkout**: Fetches the full repository history
2. **Generate Diff**: Creates a diff excluding workflow files
3. **Track Architecture**: Records changes for important PRs
4. **Summarize**: Condenses architecture log when needed
5. **Commit Changes**: Saves architecture updates back to repo
6. **Choose Model**: Selects appropriate AI model
7. **AI Review**: Performs the actual code review
8. **Post Comments**: Publishes review comments to PR
9. **Upload Artifacts**: Saves logs and responses for debugging

## Customization

### Adjusting Thresholds
- Modify `LINE_THRESHOLD` in the workflow file
- Adjust content length limits in Python scripts
- Change summarization triggers in architecture tracker

### Adding New Models
- Extend the model selection logic in `ai_review.py`
- Add new API handlers as needed
- Update payload creation functions

### Custom Filtering
- Modify file filtering logic in relevant scripts
- Add new patterns to exclude from review
- Customize architecture tracking criteria

## Best Practices

1. **Regular Monitoring**: Check workflow logs regularly
2. **API Quota Management**: Monitor API usage and limits
3. **Token Rotation**: Regularly rotate PAT tokens
4. **Architecture Reviews**: Periodically review the architecture summary
5. **Backup Strategy**: The system creates backups, but consider additional measures

## Support

For issues and contributions:
1. Check the workflow logs for error details
2. Verify all secrets are properly configured
3. Ensure API keys have sufficient quotas
4. Review the architecture summary for context
