#!/usr/bin/env python3
"""
Simple script to display current AI cost tracking information.
This can be called at any point in the workflow to show costs so far.
"""

import sys
import os

# Add the scripts directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cost_tracker import CostTracker

def main():
    """Display current cost information."""
    try:
        tracker = CostTracker()
        summary = tracker.get_summary()
        
        if summary['total_calls'] == 0:
            print("No AI calls tracked yet", file=sys.stderr)
            return
        
        tracker.print_detailed_summary()
        
        # Get detailed breakdown for review vs summary
        breakdown = tracker.get_review_summary_breakdown()
        
        # Also output costs in a format suitable for workflow step outputs
        print(f"TOTAL_COST=${summary['total_cost']:.6f}")
        print(f"TOTAL_CALLS={summary['total_calls']}")
        print(f"TOTAL_INPUT_TOKENS={summary['total_input_tokens']}")
        print(f"TOTAL_OUTPUT_TOKENS={summary['total_output_tokens']}")
        print(f"REVIEW_COST=${breakdown['review']['total_cost']:.6f}")
        print(f"SUMMARY_COST=${breakdown['summary']['total_cost']:.6f}")
        print(f"REVIEW_CALLS={breakdown['review']['total_calls']}")
        print(f"SUMMARY_CALLS={breakdown['summary']['total_calls']}")
        
        # Print key insights
        if breakdown['comparison']['review_percentage'] > 0 or breakdown['comparison']['summary_percentage'] > 0:
            print(f"REVIEW_PERCENTAGE={breakdown['comparison']['review_percentage']:.1f}")
            print(f"SUMMARY_PERCENTAGE={breakdown['comparison']['summary_percentage']:.1f}")
        
    except Exception as e:
        print(f"Error displaying costs: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
