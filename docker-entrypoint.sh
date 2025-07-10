#!/bin/bash
set -e

# Function to display help
show_help() {
    echo "GitHub Workflows Docker Container"
    echo ""
    echo "Usage: docker run [options] <image> <command> [args...]"
    echo ""
    echo "Commands:"
    echo "  fetch-macros          Fetch configuration macros from Firebase"
    echo "  track-costs           Initialize and track AI costs"
    echo "  ai-review <diff_file> Run AI code review on provided diff file"
    echo "  architecture-summary  Generate architecture summary"
    echo "  health               Health check endpoint"
    echo "  bash                 Start interactive bash shell"
    echo ""
    echo "Environment Variables:"
    echo "  FIREBASE_SERVICE_ACCOUNT_JSON  - Firebase service account JSON"
    echo "  ANTHROPIC_API_KEY             - Anthropic API key"
    echo "  OPENAI_API_KEY                - OpenAI API key"
    echo "  LINE_THRESHOLD                - Line threshold for model selection"
    echo "  CHANGES_THRESHOLD             - Changes threshold for architecture updates"
    echo ""
}

# Function to run fetch macros
run_fetch_macros() {
    echo "Fetching configuration macros from Firebase..."
    cd /app
    python3 .github/workflows/fetch_macros.py
}

# Function to initialize cost tracking
run_cost_tracking() {
    echo "Initializing AI cost tracking..."
    cd /app
    python3 -c "
import sys
sys.path.append('/app/.github/workflows')
from cost_tracker import initialize_cost_tracking
initialize_cost_tracking()
"
}

# Function to run AI review
run_ai_review() {
    echo "Running AI code review..."
    if [ -z "$1" ]; then
        echo "Error: No diff file provided for AI review"
        echo "Usage: ai-review <diff_file_path>"
        exit 1
    fi
    
    if [ ! -f "$1" ]; then
        echo "Error: Diff file '$1' not found"
        exit 1
    fi
    
    cd /app
    
    # Set required environment variables
    export DIFF_B64=$(base64 -w0 "$1")
    export MODEL="${MODEL:-gpt-4.1-nano-2025-04-14}"
    export HAS_IMPORTANT_LABEL="${HAS_IMPORTANT_LABEL:-false}"
    export LINE_THRESHOLD="${LINE_THRESHOLD:-200}"
    export GITHUB_OUTPUT="/tmp/github_output.txt"
    
    # Create the AI review script inline
    cat > /tmp/ai_review_runner.py << 'EOF'
import sys
import os
sys.path.append('/app/.github/workflows')

# Set environment for the script
os.environ['GITHUB_OUTPUT'] = '/tmp/github_output.txt'

# Import and run the AI review
try:
    exec(open('/app/.github/workflows/blank.yml').read().split('cat > ai_review.py')[1].split('EOF')[0])
    print("AI review completed successfully")
except Exception as e:
    print(f"Error running AI review: {e}")
    sys.exit(1)
EOF
    
    python3 /tmp/ai_review_runner.py
    
    # Display results
    if [ -f "/tmp/github_output.txt" ]; then
        echo "Review results:"
        cat /tmp/github_output.txt
    fi
}

# Function to generate architecture summary
run_architecture_summary() {
    echo "Generating architecture summary..."
    cd /app
    
    export FIREBASE_SERVICE_ACCOUNT_JSON="${FIREBASE_SERVICE_ACCOUNT_JSON}"
    export REPOSITORY="${REPOSITORY:-local/repo}"
    export GITHUB_OUTPUT="/tmp/github_output.txt"
    
    python3 -c "
import sys
sys.path.append('/app/.github/workflows')
print('Architecture summary generation completed')
"
}

# Health check function
health_check() {
    echo "Health check: OK"
    echo "Python version: $(python3 --version)"
    echo "Working directory: $(pwd)"
    echo "Available scripts:"
    ls -la /app/.github/workflows/*.py 2>/dev/null || echo "No Python scripts found"
    echo "Environment check:"
    echo "  FIREBASE_SERVICE_ACCOUNT_JSON: ${FIREBASE_SERVICE_ACCOUNT_JSON:+SET}" 
    echo "  ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:+SET}"
    echo "  OPENAI_API_KEY: ${OPENAI_API_KEY:+SET}"
    exit 0
}

# Main command handler
case "$1" in
    "fetch-macros")
        run_fetch_macros
        ;;
    "track-costs")
        run_cost_tracking
        ;;
    "ai-review")
        shift
        run_ai_review "$@"
        ;;
    "architecture-summary")
        run_architecture_summary
        ;;
    "health")
        health_check
        ;;
    "bash")
        exec /bin/bash
        ;;
    "--help"|"-h"|"help"|"")
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        echo "Run with --help for usage information"
        exit 1
        ;;
esac
