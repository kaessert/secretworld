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
import os
import random
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

# Load .env file from project root (search from script location, not CWD)
load_dotenv()

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
        action="count",
        default=0,
        help="Verbosity level: -v for agent decisions, -vv for full game output"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Delay between actions in seconds (default: 0)"
    )
    parser.add_argument(
        "--unlimited",
        action="store_true",
        help="Run indefinitely (ignore max-commands, use Ctrl+C to stop)"
    )
    parser.add_argument(
        "--with-ai",
        action="store_true",
        help="Require real AI generation (fails if no API key found)"
    )
    parser.add_argument(
        "--recover",
        action="store_true",
        help="Resume from last crash recovery checkpoint"
    )
    parser.add_argument(
        "--from-checkpoint",
        type=str,
        default=None,
        metavar="ID",
        help="Resume from specific checkpoint ID"
    )
    parser.add_argument(
        "--no-checkpoints",
        action="store_true",
        help="Disable automatic checkpointing"
    )
    parser.add_argument(
        "--checkpoints-dir",
        type=str,
        default="simulation_saves",
        help="Directory for checkpoint storage (default: simulation_saves)"
    )
    parser.add_argument(
        "--personality",
        type=str,
        default=None,
        choices=["cautious_explorer", "aggressive_fighter", "completionist", "speedrunner", "roleplayer"],
        help="Agent personality type (enables HumanLikeAgent)"
    )
    parser.add_argument(
        "--class",
        dest="character_class",
        type=str,
        default=None,
        choices=["warrior", "mage", "rogue", "ranger", "cleric"],
        help="Agent character class (enables HumanLikeAgent)"
    )

    args = parser.parse_args()

    # Validate API key if --with-ai is specified
    if args.with_ai:
        if not (os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")):
            print(
                "Error: --with-ai requires OPENAI_API_KEY or ANTHROPIC_API_KEY "
                "in environment or .env file"
            )
            return 1
        print(f"AI Provider: {os.getenv('AI_PROVIDER', 'auto-detect')}")

    # Import checkpoint modules if needed
    from scripts.agent_persistence import SessionManager

    # Initialize session manager
    session_manager = SessionManager(base_dir=args.checkpoints_dir)

    # Handle checkpoint recovery
    if args.recover:
        latest_session = session_manager.get_latest_session()
        if not latest_session:
            print("Error: No previous session found for recovery")
            return 1
        recovery = session_manager.get_crash_recovery(latest_session)
        if not recovery:
            print(f"Error: No crash recovery checkpoint found in session {latest_session}")
            return 1
        print(f"Recovering from crash checkpoint (command {recovery.command_index})")
        session = GameSession.from_checkpoint(
            "crash_recovery",
            session_manager=session_manager,
            max_commands=float('inf') if args.unlimited else args.max_commands,
            timeout=float('inf') if args.unlimited else args.timeout,
            verbose=args.verbose >= 1,
            show_game_output=args.verbose >= 2,
            action_delay=args.delay,
            enable_checkpoints=not args.no_checkpoints,
        )
        seed = recovery.seed
    elif args.from_checkpoint:
        print(f"Resuming from checkpoint: {args.from_checkpoint}")
        session = GameSession.from_checkpoint(
            args.from_checkpoint,
            session_manager=session_manager,
            max_commands=float('inf') if args.unlimited else args.max_commands,
            timeout=float('inf') if args.unlimited else args.timeout,
            verbose=args.verbose >= 1,
            show_game_output=args.verbose >= 2,
            action_delay=args.delay,
            enable_checkpoints=not args.no_checkpoints,
        )
        seed = session.seed
    else:
        # Use random seed if not specified
        seed = args.seed if args.seed is not None else random.randint(0, 2**31 - 1)

        # Handle unlimited mode
        max_commands = float('inf') if args.unlimited else args.max_commands
        timeout = float('inf') if args.unlimited else args.timeout

        # Create new session
        session = GameSession(
            seed=seed,
            max_commands=max_commands,
            timeout=timeout,
            verbose=args.verbose >= 1,
            show_game_output=args.verbose >= 2,
            action_delay=args.delay,
            enable_checkpoints=not args.no_checkpoints,
            session_manager=session_manager if not args.no_checkpoints else None,
            personality=args.personality,
            character_class=args.character_class,
        )

    if args.unlimited:
        print(f"Starting simulation with seed={seed}, unlimited mode (Ctrl+C to stop)")
    else:
        print(f"Starting simulation with seed={seed}, max_commands={args.max_commands}")

    # Show agent configuration if using HumanLikeAgent
    if args.personality or args.character_class:
        personality = args.personality or "cautious_explorer"
        char_class = args.character_class or "warrior"
        print(f"Agent: HumanLikeAgent (personality={personality}, class={char_class})")

    if not args.no_checkpoints:
        print(f"Checkpoints enabled (saving to {args.checkpoints_dir}/)")

    if args.delay > 0:
        print(f"Action delay: {args.delay}s")
    print("-" * 60)

    start_time = time.time()

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
    print()
    print("=== Exploration ===")
    print(f"Locations visited: {len(stats.locations_visited)}")
    print(f"Sub-locations entered: {stats.sub_locations_entered}")
    print(f"NPCs talked to: {len(stats.npcs_talked_to)}")
    print()
    print("=== Combat ===")
    print(f"Enemies defeated: {stats.enemies_defeated}")
    print(f"Bosses defeated: {stats.bosses_defeated}")
    print(f"Deaths: {stats.deaths}")
    print(f"Times fled: {stats.fled_count}")
    print()
    print("=== Quests ===")
    print(f"Quests accepted: {stats.quests_accepted}")
    print(f"Quests completed: {stats.quests_completed}")
    print()
    print("=== Resources ===")
    print(f"Potions used: {stats.potions_used}")
    print(f"Times rested: {stats.rested_count}")
    print(f"Gold earned: {stats.gold_earned}")
    print()
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
