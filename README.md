# AI Code Review System

An automated GitHub Actions-based code review system that leverages AI models (Claude 4 Sonnet and OpenAI o3-mini) to provide intelligent code analysis with context-aware architecture tracking and Firebase-powered change management.

## System Overview

This system provides automated pull request review capabilities through a sophisticated multi-component architecture that combines AI-powered code analysis with persistent architecture tracking. The system automatically selects the appropriate AI model based on change complexity and maintains a comprehensive understanding of project evolution through Firebase-backed data persistence.

## Core Components

### 1. GitHub Actions Orchestration (`/.github/workflows/blank.yml`)
The primary workflow coordinates all system operations:
- Triggers on pull request events (opened, synchronize, reopened)
- Implements security controls (blocks forks, draft PRs)
- Manages Git operations with full history access
- Orchestrates component execution with dependency management
- Handles artifact collection and debugging support

### 2. AI Review Engine (`/.github/scripts/ai_review.py`)
Central review processing component:
- Implements intelligent model selection based on PR characteristics
- Processes Git diffs with architectural context integration
- Handles API communication for both Claude and OpenAI services
- Provides content filtering and size optimization
- Manages error handling and fallback scenarios

### 3. Firebase Integration Layer
Multiple components manage persistent data:

**Firebase Client (`/.github/scripts/firebase_client.py`)**
- Provides unified Firebase Firestore access
- Manages authentication and connection handling
- Implements data operations for architecture summaries and changes
- Handles error recovery and retry logic

**Architecture Tracker (`/.github/scripts/track_architecture.py`)**
- Records significant architectural changes in Firebase
- Manages change counting and summarization triggers
- Associates changes with PR metadata
- Determines when architectural summaries require regeneration

**Context Fetcher (`/.github/scripts/fetch_firebase_context.py`)**
- Retrieves architectural context for review operations
- Manages local file integration with Firebase data
- Provides fallback mechanisms for Firebase unavailability
- Handles data encoding for workflow integration

**Architecture Summarizer (`/.github/scripts/summarize_architecture.py`)**
- Generates comprehensive project architecture summaries
- Analyzes entire codebase for new projects
- Updates existing summaries with incremental changes
- Utilizes Claude for natural language architecture documentation

### 4. Comment Management System (`/.github/scripts/post_comments.py`)
GitHub integration component:
- Parses AI-generated review responses
- Posts line-by-line comments to pull requests
- Handles JSON formatting and error recovery
- Generates summary comments with review statistics
- Manages GitHub API rate limiting and permissions

## Prerequisites and Configuration

### Required GitHub Repository Secrets

Configure these secrets in repository Settings > Secrets and variables > Actions:

**AI Service Authentication:**
- `ANTHROPIC_API_KEY`: Anthropic API key for Claude model access
- `OPENAI_API_KEY`: OpenAI API key for o3-mini model access

**GitHub Access:**
- `PAT_TOKEN`: Personal Access Token with permissions:
  - `repo` (full repository access)
  - `contents` (read and write access)
  - `pull-requests` (write access for comments)

**Firebase Configuration:**
- `FIREBASE_PROJECT_ID`: Firebase project identifier
- `FIREBASE_PRIVATE_KEY`: Firebase service account private key
- `FIREBASE_CLIENT_EMAIL`: Firebase service account client email

### Firebase Service Account Setup

1. Create a Firebase project or use existing project
2. Generate a service account key in Firebase Console:
   - Go to Project Settings > Service Accounts
   - Generate new private key
   - Extract the required fields for GitHub secrets
3. Place the complete service account JSON file at:
   `/.github/pr-agent-21ba8-firebase-adminsdk-fbsvc-95c716d6e2.json`

### Personal Access Token Configuration

1. Navigate to GitHub Settings > Developer settings > Personal access tokens
2. Generate new token (classic) with required permissions
3. Configure as `PAT_TOKEN` repository secret

## Deployment Instructions

### Repository Structure Setup

Create the following directory structure:

```
.github/
├── workflows/
│   └── blank.yml
├── scripts/
│   ├── ai_review.py
│   ├── firebase_client.py
│   ├── fetch_firebase_context.py
│   ├── post_comments.py
│   ├── summarize_architecture.py
│   └── track_architecture.py
└── pr-agent-21ba8-firebase-adminsdk-fbsvc-95c716d6e2.json
```

### Python Dependencies

The system automatically installs required packages:
- `firebase-admin`: Firebase Firestore integration
- `anthropic`: Claude API client
- `openai`: OpenAI API client

### Environment Configuration

Modify workflow environment variables as needed:

```yaml
env:
  LINE_THRESHOLD: 200                    # Lines changed threshold for Claude selection
  IMPORTANT_CHANGE_MARKERS: '#IMPORTANT-CHANGE,#IMPORTANT-CHANGES'
  IMPORTANT_CHANGE_LABELS: 'important change,important changes'
```

## Operational Procedures

### Standard Code Review Process

1. System automatically activates on pull request creation or updates
2. Generates diff excluding workflow files and sensitive directories
3. Selects appropriate AI model based on change characteristics
4. Retrieves architectural context from Firebase
5. Performs AI-powered code analysis
6. Posts line-by-line comments and summary to pull request

### Architecture Change Tracking

For significant architectural modifications:

1. Add `#IMPORTANT-CHANGE` marker to pull request title, or
2. Apply `important changes` label to pull request
3. System automatically:
   - Records changes in Firebase with metadata
   - Increments change counter
   - Triggers summarization when threshold reached
   - Updates architectural documentation

### Model Selection Algorithm

**Claude 4 Sonnet Selection Criteria:**
- Pull request contains important change markers in title
- Pull request has important change labels applied
- Modified lines exceed configured threshold (default: 200)

**OpenAI o3-mini Selection Criteria:**
- Pull request modifications below threshold
- Standard maintenance and bug fix changes
- No importance indicators present

## System Features

### Intelligent Context Management

**Architectural Context Integration:**
- Maintains project architecture understanding through Firebase
- Provides historical context for review decisions
- Automatically creates architecture summaries for new projects
- Updates documentation based on accumulated changes

**Content-Aware Processing:**
- Excludes workflow files from review to prevent recursive modifications
- Filters build artifacts and temporary files
- Focuses analysis on meaningful code changes
- Implements size limits to manage API costs

### Error Handling and Resilience

**API Failure Management:**
- Implements exponential backoff for transient failures
- Provides fallback mechanisms for service unavailability
- Continues workflow execution with degraded functionality
- Extensive logging for troubleshooting

**Data Integrity Protection:**
- Creates timestamped backups before summarization
- Validates JSON responses with error recovery
- Handles malformed AI responses gracefully
- Maintains audit trail of all operations

### Security Implementation

**Access Control:**
- Prevents execution on forked repositories
- Blocks processing of draft pull requests
- Uses secure secret management for API keys
- Implements permission validation

**Data Protection:**
- Excludes sensitive files from analysis
- Manages API payload sizes to prevent data exposure
- Implements secure base64 encoding for data transfer
- Validates input parameters and file paths

## Performance Optimization

### API Efficiency
- Truncates large files to prevent token limit exceeding
- Implements payload size monitoring and warnings
- Optimizes prompt engineering for token usage
- Batches operations where possible

### Firebase Optimization
- Uses efficient Firestore queries with proper indexing
- Implements connection pooling and reuse
- Limits data retrieval to essential information
- Manages collection structures for optimal performance

## Troubleshooting Guide

### Common Configuration Issues

**Authentication Failures:**
- Verify all required secrets are properly configured
- Check Firebase service account permissions
- Validate API key quotas and billing status
- Ensure PAT token has sufficient repository permissions

**Review Processing Failures:**
- Monitor workflow execution logs for detailed error information
- Check API response status and error messages
- Verify diff generation and content filtering
- Validate JSON parsing and response formatting

**Firebase Connectivity Issues:**
- Confirm Firebase project configuration
- Check service account key validity
- Verify Firestore database rules and permissions
- Monitor Firebase quota usage and billing

### Debugging Procedures

**Workflow Diagnostics:**
- Examine GitHub Actions workflow logs
- Review uploaded artifacts for detailed responses
- Check step execution status and conditional logic
- Monitor resource usage and timeout issues

**Component-Level Debugging:**
- Enable verbose logging in Python scripts
- Examine temporary files created during execution
- Validate environment variable configuration
- Test Firebase connectivity independently

**Performance Analysis:**
- Monitor API response times and payload sizes
- Analyze token usage patterns
- Review Firebase operation efficiency
- Check GitHub API rate limit consumption

## Customization Options

### Threshold Adjustment
Modify review sensitivity by adjusting:
- `LINE_THRESHOLD`: Change detection sensitivity
- Firebase summarization triggers
- Content length limits for API calls
- File size limits for analysis

### Model Configuration
Extend AI model support:
- Add new model providers to `ai_review.py`
- Implement custom payload formatting
- Configure model-specific parameters
- Update selection logic algorithms

### Architecture Tracking Customization
Configure change detection:
- Modify importance detection patterns
- Adjust summarization frequency
- Customize Firebase data structures
- Implement custom change categorization

## Maintenance Procedures

### Regular Operations
- Monitor API usage and costs
- Review Firebase storage utilization
- Update dependencies and security patches
- Validate backup and recovery procedures

### Scaling Considerations
- Monitor GitHub Actions usage quotas
- Plan for increased Firebase data volumes
- Consider API rate limiting impacts
- Implement monitoring and alerting systems

This system provides a comprehensive, production-ready solution for automated code review with persistent architectural understanding, suitable for teams requiring consistent code quality enforcement with minimal manual intervention.
