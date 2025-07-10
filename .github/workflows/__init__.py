# This file makes the .github/workflows directory a Python package
# This allows importing modules like cost_tracker from within the package

"""
GitHub Workflows Package

This package contains various utilities and modules for GitHub Actions workflows,
including cost tracking, Firebase operations, AI review processes, and more.
"""

__version__ = "1.0.0"
__author__ = "Your Name"

# Import main modules to make them available at package level
try:
    from . import cost_tracker
    from . import firebase_client
    from . import ai_review
    from . import debug_firebase
    from . import display_costs
    from . import fetch_firebase_context
    from . import fetch_macros
    from . import parse_pr_macros
    from . import post_comments
    from . import summarize_architecture
    from . import test_firebase
    from . import track_architecture
except ImportError as e:
    # Handle import errors gracefully for optional dependencies
    print(f"Warning: Could not import some modules: {e}")

# Define what gets imported with "from workflows import *"
__all__ = [
    'cost_tracker',
    'firebase_client', 
    'ai_review',
    'debug_firebase',
    'display_costs',
    'fetch_firebase_context',
    'fetch_macros',
    'parse_pr_macros',
    'post_comments',
    'summarize_architecture',
    'test_firebase',
    'track_architecture'
]

# Package metadata
__package_name__ = "github_workflows"
__description__ = "Utilities and modules for GitHub Actions workflows"
