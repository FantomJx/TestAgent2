import json
import os
import sys
from datetime import datetime
from typing import Dict, Optional, Tuple


class CostTracker:
    """Track AI usage costs for Claude and OpenAI models."""

    # Pricing per 1 million tokens
    PRICING = {
        'claude-sonnet-4-20250514': {
            'input': 3.00,   # $3/MTok
            'output': 15.00  # $15/MTok
        },
        'o3-mini': {
            'input': 1.10,   # $1.10/MTok
            'output': 4.40   # $4.40/MTok
        },
        'gpt-4.1-nano-2025-04-14': {
            'input': 0.10,   # $0.50/MTok (estimated pricing)
            'output': 0.40   # $2.00/MTok (estimated pricing)
        }
    }

    def __init__(self):
        self.cost_file = '/tmp/ai_costs.json'
        self.costs = self._load_costs()

    def _load_costs(self) -> Dict:
        """Load existing cost data or initialize empty structure."""
        if os.path.exists(self.cost_file):
            try:
                with open(self.cost_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(
                    f"Warning: Could not load existing costs: {e}", file=sys.stderr)

        return {
            'total_cost': 0.0,
            'calls': []
        }

    def _save_costs(self):
        """Save cost data to file."""
        try:
            with open(self.cost_file, 'w') as f:
                json.dump(self.costs, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save costs: {e}", file=sys.stderr)

    def extract_token_usage(self, response_data: Dict, model: str) -> Tuple[int, int]:
        """Extract input and output tokens from API response."""
        input_tokens = 0
        output_tokens = 0

        try:
            if model.startswith('claude'):
                # Claude response format
                usage = response_data.get('usage', {})
                input_tokens = usage.get('input_tokens', 0)
                output_tokens = usage.get('output_tokens', 0)
            else:
                # OpenAI response format
                usage = response_data.get('usage', {})
                input_tokens = usage.get('prompt_tokens', 0)
                output_tokens = usage.get('completion_tokens', 0)
        except Exception as e:
            print(
                f"Warning: Could not extract token usage: {e}", file=sys.stderr)

        return input_tokens, output_tokens

    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for given model and token usage."""
        if model not in self.PRICING:
            print(
                f"Warning: Unknown model {model}, cost calculation may be inaccurate", file=sys.stderr)
            return 0.0

        pricing = self.PRICING[model]

        # Convert tokens to millions and calculate cost
        input_cost = (input_tokens / 1_000_000) * pricing['input']
        output_cost = (output_tokens / 1_000_000) * pricing['output']

        return input_cost + output_cost

    def track_api_call(self, model: str, response_data: Dict, call_type: str = "review",
                       context: Optional[str] = None):
        """Track an API call and calculate its cost."""
        input_tokens, output_tokens = self.extract_token_usage(
            response_data, model)
        cost = self.calculate_cost(model, input_tokens, output_tokens)

        # Add timestamp for better tracking
        timestamp = datetime.now().isoformat()

        call_data = {
            'model': model,
            'call_type': call_type,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'cost': cost,
            'context': context,
            'timestamp': timestamp
        }

        self.costs['calls'].append(call_data)
        self.costs['total_cost'] += cost

        # Log the cost information with more detail
        print(f"AI Cost Tracking - {call_type.upper()}:", file=sys.stderr)
        print(f"  Model: {model}", file=sys.stderr)
        print(f"  Input tokens: {input_tokens:,}", file=sys.stderr)
        print(f"  Output tokens: {output_tokens:,}", file=sys.stderr)
        print(f"  Cost: ${cost:.6f}", file=sys.stderr)
        print(f"  Time: {timestamp}", file=sys.stderr)
        if context:
            print(f"  Context: {context}", file=sys.stderr)

        self._save_costs()
        return cost

    def get_summary(self) -> Dict:
        """Get cost summary for display."""
        total_input_tokens = sum(call['input_tokens']
                                 for call in self.costs['calls'])
        total_output_tokens = sum(call['output_tokens']
                                  for call in self.costs['calls'])

        # Group by model
        by_model = {}
        for call in self.costs['calls']:
            model = call['model']
            if model not in by_model:
                by_model[model] = {
                    'calls': 0,
                    'input_tokens': 0,
                    'output_tokens': 0,
                    'cost': 0.0
                }
            by_model[model]['calls'] += 1
            by_model[model]['input_tokens'] += call['input_tokens']
            by_model[model]['output_tokens'] += call['output_tokens']
            by_model[model]['cost'] += call['cost']

        # Group by call type
        by_type = {}
        for call in self.costs['calls']:
            call_type = call['call_type']
            if call_type not in by_type:
                by_type[call_type] = {
                    'calls': 0,
                    'input_tokens': 0,
                    'output_tokens': 0,
                    'cost': 0.0
                }
            by_type[call_type]['calls'] += 1
            by_type[call_type]['input_tokens'] += call['input_tokens']
            by_type[call_type]['output_tokens'] += call['output_tokens']
            by_type[call_type]['cost'] += call['cost']

        return {
            'total_cost': self.costs['total_cost'],
            'total_calls': len(self.costs['calls']),
            'total_input_tokens': total_input_tokens,
            'total_output_tokens': total_output_tokens,
            'by_model': by_model,
            'by_type': by_type,
            'individual_calls': self.costs['calls']
        }

    def print_detailed_summary(self):
        """Print a detailed cost summary to stderr."""
        summary = self.get_summary()

        print("\n" + "="*80, file=sys.stderr)
        print("AI USAGE COST SUMMARY", file=sys.stderr)
        print("="*80, file=sys.stderr)

        # Overall summary
        print(f"Total Cost: ${summary['total_cost']:.6f}", file=sys.stderr)
        print(f"Total API Calls: {summary['total_calls']}", file=sys.stderr)
        print(
            f"Total Input Tokens: {summary['total_input_tokens']:,}", file=sys.stderr)
        print(
            f"Total Output Tokens: {summary['total_output_tokens']:,}", file=sys.stderr)
        print(
            f"Total Tokens: {summary['total_input_tokens'] + summary['total_output_tokens']:,}", file=sys.stderr)

        # Average cost per call
        if summary['total_calls'] > 0:
            avg_cost = summary['total_cost'] / summary['total_calls']
            avg_tokens = (summary['total_input_tokens'] +
                          summary['total_output_tokens']) / summary['total_calls']
            print(f"Average Cost per Call: ${avg_cost:.6f}", file=sys.stderr)
            print(
                f"Average Tokens per Call: {avg_tokens:,.0f}", file=sys.stderr)

        # Highlight review vs summary costs
        review_data = summary['by_type'].get(
            'review', {'cost': 0.0, 'calls': 0})

        # Aggregate all summary-related call types (any type containing "summary" or "summarize")
        summary_data = {'cost': 0.0, 'calls': 0,
                        'input_tokens': 0, 'output_tokens': 0}
        for call_type, type_data in summary['by_type'].items():
            if 'summary' in call_type.lower() or call_type.lower() == 'summarize':
                summary_data['cost'] += type_data['cost']
                summary_data['calls'] += type_data['calls']
                summary_data['input_tokens'] += type_data['input_tokens']
                summary_data['output_tokens'] += type_data['output_tokens']

        print(f"\nREVIEW vs SUMMARY BREAKDOWN:", file=sys.stderr)
        print("-" * 50, file=sys.stderr)
        print(f"Review Operations:", file=sys.stderr)
        print(
            f"   Cost: ${review_data['cost']:.6f} ({(review_data['cost']/summary['total_cost']*100 if summary['total_cost'] > 0 else 0):.1f}%)", file=sys.stderr)
        print(f"   Calls: {review_data['calls']}", file=sys.stderr)
        print(
            f"   Input: {review_data.get('input_tokens', 0):,} tokens", file=sys.stderr)
        print(
            f"   Output: {review_data.get('output_tokens', 0):,} tokens", file=sys.stderr)

        print(f"Summary Operations:", file=sys.stderr)
        print(
            f"   Cost: ${summary_data['cost']:.6f} ({(summary_data['cost']/summary['total_cost']*100 if summary['total_cost'] > 0 else 0):.1f}%)", file=sys.stderr)
        print(f"   Calls: {summary_data['calls']}", file=sys.stderr)
        print(
            f"   Input: {summary_data.get('input_tokens', 0):,} tokens", file=sys.stderr)
        print(
            f"   Output: {summary_data.get('output_tokens', 0):,} tokens", file=sys.stderr)

        print(f"\nCOST BY MODEL:", file=sys.stderr)
        print("-" * 50, file=sys.stderr)
        for model, data in summary['by_model'].items():
            percentage = (data['cost']/summary['total_cost']
                          * 100 if summary['total_cost'] > 0 else 0)
            efficiency = data['cost'] / (data['input_tokens'] + data['output_tokens']) * 1000000 if (
                data['input_tokens'] + data['output_tokens']) > 0 else 0
            print(f"{model}:", file=sys.stderr)
            print(
                f"   Cost: ${data['cost']:.6f} ({percentage:.1f}%)", file=sys.stderr)
            print(f"   Calls: {data['calls']}", file=sys.stderr)
            print(
                f"   Input: {data['input_tokens']:,} tokens", file=sys.stderr)
            print(
                f"   Output: {data['output_tokens']:,} tokens", file=sys.stderr)
            print(
                f"   Efficiency: ${efficiency:.2f} per MTok", file=sys.stderr)

        print(f"\nCOST BY OPERATION TYPE:", file=sys.stderr)
        print("-" * 50, file=sys.stderr)
        for op_type, data in summary['by_type'].items():
            percentage = (data['cost']/summary['total_cost']
                          * 100 if summary['total_cost'] > 0 else 0)
            print(f"{op_type.upper()}:", file=sys.stderr)
            print(
                f"   Cost: ${data['cost']:.6f} ({percentage:.1f}%)", file=sys.stderr)
            print(f"   Calls: {data['calls']}", file=sys.stderr)
            print(
                f"   Input: {data['input_tokens']:,} tokens", file=sys.stderr)
            print(
                f"   Output: {data['output_tokens']:,} tokens", file=sys.stderr)
            if data['calls'] > 0:
                avg_cost_per_call = data['cost'] / data['calls']
                print(
                    f"   Avg Cost/Call: ${avg_cost_per_call:.6f}", file=sys.stderr)

        # Cost trends and insights
        if len(summary['individual_calls']) > 1:
            print(f"\nCOST INSIGHTS:", file=sys.stderr)
            print("-" * 50, file=sys.stderr)

            # Most expensive call
            most_expensive = max(
                summary['individual_calls'], key=lambda x: x['cost'])
            print(
                f"Most Expensive Call: {most_expensive['call_type']} - ${most_expensive['cost']:.6f}", file=sys.stderr)

            # Most token-heavy call
            token_heavy = max(summary['individual_calls'],
                              key=lambda x: x['input_tokens'] + x['output_tokens'])
            total_tokens = token_heavy['input_tokens'] + \
                token_heavy['output_tokens']
            print(
                f"Most Token-Heavy Call: {token_heavy['call_type']} - {total_tokens:,} tokens", file=sys.stderr)

            # Cost per operation type efficiency
            if len(summary['by_type']) > 1:
                print(f"Operation Efficiency ($/call):", file=sys.stderr)
                for op_type, data in sorted(summary['by_type'].items(),
                                            key=lambda x: x[1]['cost'] /
                                            x[1]['calls'] if x[1]['calls'] > 0 else 0,
                                            reverse=True):
                    if data['calls'] > 0:
                        efficiency = data['cost'] / data['calls']
                        print(f"   {op_type}: ${efficiency:.6f}",
                              file=sys.stderr)

        if summary['individual_calls'] and len(summary['individual_calls']) <= 10:
            print(f"\nINDIVIDUAL CALLS:", file=sys.stderr)
            print("-" * 50, file=sys.stderr)
            for i, call in enumerate(summary['individual_calls'], 1):
                timestamp = call.get('timestamp', 'Unknown')
                if timestamp != 'Unknown':
                    try:
                        dt = datetime.fromisoformat(
                            timestamp.replace('Z', '+00:00'))
                        time_str = dt.strftime('%H:%M:%S')
                    except:
                        time_str = timestamp[:19] if len(
                            timestamp) > 19 else timestamp
                else:
                    time_str = 'Unknown'

                total_tokens = call['input_tokens'] + call['output_tokens']
                print(
                    f"{i:2d}. {time_str} | {call['call_type'].upper()} | {call['model']}", file=sys.stderr)
                print(
                    f"    {call['input_tokens']:,} in, {call['output_tokens']:,} out | ${call['cost']:.6f}", file=sys.stderr)
                if call.get('context'):
                    context_preview = call['context'][:50] + \
                        "..." if len(call['context']) > 50 else call['context']
                    print(f"    {context_preview}", file=sys.stderr)

        print("="*80, file=sys.stderr)

    def get_review_summary_breakdown(self) -> Dict:
        """Get detailed breakdown of review vs summary operations."""
        review_calls = [call for call in self.costs['calls']
                        if call['call_type'] == 'review']
        # Match any call type that contains "summary" (case-insensitive)
        summary_calls = [call for call in self.costs['calls'] if
                         'summary' in call['call_type'].lower() or call['call_type'].lower() == 'summarize']

        def calculate_stats(calls):
            if not calls:
                return {
                    'total_cost': 0.0,
                    'total_calls': 0,
                    'total_input_tokens': 0,
                    'total_output_tokens': 0,
                    'avg_cost_per_call': 0.0,
                    'avg_tokens_per_call': 0.0,
                    'most_expensive_call': None,
                    'models_used': {}
                }

            total_cost = sum(call['cost'] for call in calls)
            total_input = sum(call['input_tokens'] for call in calls)
            total_output = sum(call['output_tokens'] for call in calls)
            total_calls = len(calls)

            # Model breakdown
            models = {}
            for call in calls:
                model = call['model']
                if model not in models:
                    models[model] = {'calls': 0, 'cost': 0.0, 'tokens': 0}
                models[model]['calls'] += 1
                models[model]['cost'] += call['cost']
                models[model]['tokens'] += call['input_tokens'] + \
                    call['output_tokens']

            return {
                'total_cost': total_cost,
                'total_calls': total_calls,
                'total_input_tokens': total_input,
                'total_output_tokens': total_output,
                'avg_cost_per_call': total_cost / total_calls,
                'avg_tokens_per_call': (total_input + total_output) / total_calls,
                'most_expensive_call': max(calls, key=lambda x: x['cost']),
                'models_used': models
            }

        review_stats = calculate_stats(review_calls)
        summary_stats = calculate_stats(summary_calls)

        total_cost = self.costs['total_cost']

        return {
            'review': review_stats,
            'summary': summary_stats,
            'comparison': {
                'review_percentage': (review_stats['total_cost'] / total_cost * 100) if total_cost > 0 else 0,
                'summary_percentage': (summary_stats['total_cost'] / total_cost * 100) if total_cost > 0 else 0,
                'cost_ratio': (review_stats['total_cost'] / summary_stats['total_cost']) if summary_stats['total_cost'] > 0 else float('inf'),
                'efficiency_comparison': {
                    'review_cost_per_token': review_stats['total_cost'] / (review_stats['total_input_tokens'] + review_stats['total_output_tokens']) if (review_stats['total_input_tokens'] + review_stats['total_output_tokens']) > 0 else 0,
                    'summary_cost_per_token': summary_stats['total_cost'] / (summary_stats['total_input_tokens'] + summary_stats['total_output_tokens']) if (summary_stats['total_input_tokens'] + summary_stats['total_output_tokens']) > 0 else 0
                }
            }
        }

    def print_quick_summary(self):
        """Print a concise cost summary for quick reference."""
        summary = self.get_summary()
        breakdown = self.get_review_summary_breakdown()

        print(
            f"TOTAL COST: ${summary['total_cost']:.6f} | Calls: {summary['total_calls']} | Tokens: {summary['total_input_tokens'] + summary['total_output_tokens']:,}", file=sys.stderr)

        if breakdown['review']['total_calls'] > 0:
            print(
                f"Review: ${breakdown['review']['total_cost']:.6f} ({breakdown['comparison']['review_percentage']:.1f}%) | {breakdown['review']['total_calls']} calls", file=sys.stderr)

        if breakdown['summary']['total_calls'] > 0:
            print(
                f"Summary: ${breakdown['summary']['total_cost']:.6f} ({breakdown['comparison']['summary_percentage']:.1f}%) | {breakdown['summary']['total_calls']} calls", file=sys.stderr)


def initialize_cost_tracking():
    """Initialize cost tracking for the workflow."""
    # Clear any existing cost data for this run
    cost_file = '/tmp/ai_costs.json'
    if os.path.exists(cost_file):
        os.remove(cost_file)

    tracker = CostTracker()
    print("AI cost tracking initialized", file=sys.stderr)
    return tracker


def finalize_cost_tracking():
    """Print final cost summary and save to GitHub Actions output."""
    tracker = CostTracker()
    tracker.print_detailed_summary()

    summary = tracker.get_summary()
    breakdown = tracker.get_review_summary_breakdown()

    # Save summary to GitHub Actions output if available
    if 'GITHUB_OUTPUT' in os.environ:
        with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
            fh.write(f"total_ai_cost={summary['total_cost']:.6f}\n")
            fh.write(f"total_ai_calls={summary['total_calls']}\n")
            fh.write(f"total_input_tokens={summary['total_input_tokens']}\n")
            fh.write(f"total_output_tokens={summary['total_output_tokens']}\n")
            fh.write(f"review_cost={breakdown['review']['total_cost']:.6f}\n")
            fh.write(
                f"summary_cost={breakdown['summary']['total_cost']:.6f}\n")
            fh.write(f"review_calls={breakdown['review']['total_calls']}\n")
            fh.write(f"summary_calls={breakdown['summary']['total_calls']}\n")

    # Also save a human-readable summary to a file for artifacts
    try:
        with open('/tmp/ai_cost_summary.txt', 'w') as f:
            f.write("AI USAGE COST SUMMARY\n")
            f.write("="*80 + "\n\n")
            f.write(f"Total Cost: ${summary['total_cost']:.6f}\n")
            f.write(f"Total API Calls: {summary['total_calls']}\n")
            f.write(f"Total Input Tokens: {summary['total_input_tokens']:,}\n")
            f.write(
                f"Total Output Tokens: {summary['total_output_tokens']:,}\n\n")

            f.write("REVIEW vs SUMMARY BREAKDOWN:\n")
            f.write("-" * 50 + "\n")
            f.write(f"Review Operations:\n")
            f.write(
                f"   Cost: ${breakdown['review']['total_cost']:.6f} ({breakdown['comparison']['review_percentage']:.1f}%)\n")
            f.write(f"   Calls: {breakdown['review']['total_calls']}\n")
            f.write(
                f"   Input: {breakdown['review']['total_input_tokens']:,} tokens\n")
            f.write(
                f"   Output: {breakdown['review']['total_output_tokens']:,} tokens\n\n")

            f.write(f"Summary Operations:\n")
            f.write(
                f"   Cost: ${breakdown['summary']['total_cost']:.6f} ({breakdown['comparison']['summary_percentage']:.1f}%)\n")
            f.write(f"   Calls: {breakdown['summary']['total_calls']}\n")
            f.write(
                f"   Input: {breakdown['summary']['total_input_tokens']:,} tokens\n")
            f.write(
                f"   Output: {breakdown['summary']['total_output_tokens']:,} tokens\n\n")

            f.write("COST BY MODEL:\n")
            f.write("-" * 50 + "\n")
            for model, data in summary['by_model'].items():
                percentage = (data['cost']/summary['total_cost']
                              * 100 if summary['total_cost'] > 0 else 0)
                f.write(f"{model}:\n")
                f.write(f"   Cost: ${data['cost']:.6f} ({percentage:.1f}%)\n")
                f.write(f"   Calls: {data['calls']}\n")
                f.write(f"   Input: {data['input_tokens']:,} tokens\n")
                f.write(f"   Output: {data['output_tokens']:,} tokens\n\n")

            f.write("COST BY OPERATION TYPE:\n")
            f.write("-" * 50 + "\n")
            for op_type, data in summary['by_type'].items():
                percentage = (data['cost']/summary['total_cost']
                              * 100 if summary['total_cost'] > 0 else 0)
                f.write(f"{op_type.upper()}:\n")
                f.write(f"   Cost: ${data['cost']:.6f} ({percentage:.1f}%)\n")
                f.write(f"   Calls: {data['calls']}\n")
                f.write(f"   Input: {data['input_tokens']:,} tokens\n")
                f.write(f"   Output: {data['output_tokens']:,} tokens\n")
                if data['calls'] > 0:
                    avg_cost_per_call = data['cost'] / data['calls']
                    f.write(f"   Avg Cost/Call: ${avg_cost_per_call:.6f}\n")
                f.write("\n")

            if summary['individual_calls']:
                f.write("INDIVIDUAL CALLS:\n")
                f.write("-" * 50 + "\n")
                for i, call in enumerate(summary['individual_calls'], 1):
                    timestamp = call.get('timestamp', 'Unknown')
                    f.write(
                        f"{i:2d}. {call['call_type'].upper()} - {call['model']}\n")
                    f.write(
                        f"    {call['input_tokens']:,} in, {call['output_tokens']:,} out | ${call['cost']:.6f}\n")
                    f.write(f"    {timestamp}\n")
                    if call.get('context'):
                        f.write(f"    {call['context']}\n")
                    f.write("\n")
    except Exception as e:
        print(
            f"Warning: Could not save human-readable summary: {e}", file=sys.stderr)

    return summary


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='AI Cost Tracker')
    parser.add_argument('--quick', '-q', action='store_true',
                        help='Show quick summary')
    parser.add_argument('--breakdown', '-b', action='store_true',
                        help='Show review vs summary breakdown')
    parser.add_argument('--reset', '-r', action='store_true',
                        help='Reset cost tracking data')
    args = parser.parse_args()

    tracker = CostTracker()

    if args.reset:
        cost_file = '/tmp/ai_costs.json'
        if os.path.exists(cost_file):
            os.remove(cost_file)
            print("Cost tracking data reset", file=sys.stderr)
        else:
            print("No cost data to reset", file=sys.stderr)
    elif args.quick:
        tracker.print_quick_summary()
    elif args.breakdown:
        breakdown = tracker.get_review_summary_breakdown()
        summary = tracker.get_summary()
        print(f"\nREVIEW vs SUMMARY COST BREAKDOWN:", file=sys.stderr)
        print("="*60, file=sys.stderr)
        print(f"TOTAL COST: ${summary['total_cost']:.6f}", file=sys.stderr)
        print("-" * 60, file=sys.stderr)
        print(
            f"Review Operations: ${breakdown['review']['total_cost']:.6f} ({breakdown['comparison']['review_percentage']:.1f}%)", file=sys.stderr)
        print(
            f"Summary Operations: ${breakdown['summary']['total_cost']:.6f} ({breakdown['comparison']['summary_percentage']:.1f}%)", file=sys.stderr)

        if breakdown['comparison']['cost_ratio'] != float('inf'):
            print(
                f"Review/Summary Cost Ratio: {breakdown['comparison']['cost_ratio']:.2f}x", file=sys.stderr)

        if breakdown['comparison']['efficiency_comparison']['review_cost_per_token'] > 0:
            print(
                f"Review Cost per Token: ${breakdown['comparison']['efficiency_comparison']['review_cost_per_token']*1000000:.2f}/MTok", file=sys.stderr)
        if breakdown['comparison']['efficiency_comparison']['summary_cost_per_token'] > 0:
            print(
                f"Summary Cost per Token: ${breakdown['comparison']['efficiency_comparison']['summary_cost_per_token']*1000000:.2f}/MTok", file=sys.stderr)
    else:
        tracker.print_detailed_summary()
