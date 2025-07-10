# This file makes the .github/workflows directory a Python package
# This allows importing modules like cost_tracker from within the package

"""
GitHub Workflows Package

This package contains various utilities and modules for GitHub Actions workflows,
including cost tracking, Firebase operations, AI review processes, and more.
"""

__version__ = "1.0.0"
__author__ = "Your Name"

# List of expected modules
_EXPECTED_MODULES = [
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

# Import main modules to make them available at package level
_available_modules = []
_missing_modules = []

for module_name in _EXPECTED_MODULES:
    try:
        module = __import__(f'.{module_name}', package=__name__, level=0)
        _available_modules.append(module_name)
        # Make the module available at package level
        globals()[module_name] = getattr(module, module_name, module)
    except ImportError:
        _missing_modules.append(module_name)

# Only show warning if we're not in a GitHub Actions environment
import os
if _missing_modules and not os.getenv('GITHUB_ACTIONS'):
    print(f"Info: Some workflow modules are not available: {', '.join(_missing_modules)}")
    print(f"Available modules: {', '.join(_available_modules) if _available_modules else 'None'}")

# Define what gets imported with "from workflows import *"
__all__ = _available_modules

# Package metadata
__package_name__ = "github_workflows"
__description__ = "Utilities and modules for GitHub Actions workflows"
