#!/usr/bin/env python3
"""Run CLI-RPG simulation with AI agent.

This script launches an autonomous AI agent to play CLI-RPG via JSON mode.
It collects statistics and reports on the session.

Usage:
    python -m scripts.run_simulation [options]

Examples:
    python -m scripts.run_simulation --seed=42 --max-commands=100 --verbose
    python -m scripts.run_simulation --output=report.json
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.ai_agent import GameSession


def main() -> int:
    """Run simulation and report results.

    Returns:
        Exit code (0 for success, 1 for errors)
    """
    parser = argparse.ArgumentParser(
        description="Run CLI-RPG simulation with AI agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m scripts.run_simulation --seed=42 --max-commands=100
  python -m scripts.run_simulation --verbose --output=report.json
        """
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="RNG seed for reproducibility (default: random)"
    )
    parser.add_argument(
        "--max-commands",
        type=int,
        default=1000,
        help="Maximum commands to issue (default: 1000)"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=300.0,
        help="Session timeout in seconds (default: 300)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output JSON report to file"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print agent decisions"
    )

    args = parser.parse_args()

    # Use random seed if not specified
    seed = args.seed if args.seed is not None else random.randint(0, 2**31 - 1)

    print(f"Starting simulation with seed={seed}, max_commands={args.max_commands}")
    print("-" * 60)

    start_time = time.time()

    # Create and run session
    session = GameSession(
        seed=seed,
        max_commands=args.max_commands,
        timeout=args.timeout,
        verbose=args.verbose,
    )

    try:
        stats = session.run()
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user")
        session.stop()
        return 1
    except Exception as e:
        print(f"\nSimulation error: {e}")
        return 1

    elapsed = time.time() - start_time

    # Print summary
    print("-" * 60)
    print("Simulation Complete")
    print("-" * 60)
    print(f"Duration: {elapsed:.1f}s")
    print(f"Commands issued: {stats.commands_issued}")
    print(f"Locations visited: {len(stats.locations_visited)}")
    print(f"Enemies defeated: {stats.enemies_defeated}")
    print(f"Deaths: {stats.deaths}")
    print(f"Potions used: {stats.potions_used}")
    print(f"Times fled: {stats.fled_count}")
    print(f"Times rested: {stats.rested_count}")
    print(f"Gold earned: {stats.gold_earned}")
    print(f"Errors encountered: {stats.errors_encountered}")

    # Output to file if requested
    if args.output:
        report = {
            "seed": seed,
            "duration_seconds": elapsed,
            "config": {
                "max_commands": args.max_commands,
                "timeout": args.timeout,
            },
            "stats": stats.to_dict(),
        }
        output_path = Path(args.output)
        output_path.write_text(json.dumps(report, indent=2))
        print(f"\nReport saved to: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
