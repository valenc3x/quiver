"""CLI interface for Quiver."""

import argparse
import sys
from pathlib import Path
from typing import Optional

from . import __version__
from .parser import parse_file
from .selector import select_random_available
from .state import pick_and_mark, save_state, validate_history, find_entry_by_index
from .rollback import rollback_last, reset_all


def cmd_pick(args) -> int:
    """
    Pick a random unused entry.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # Parse the file
        parsed = parse_file(args.file)

        # Validate history
        validate_history(parsed)

        # Get history
        history = parsed.metadata.get('history', [])

        # Select a random available entry
        entry = select_random_available(parsed.entries, history)

        if entry is None:
            print("❌ No unused entries available.")
            print("   Use 'quiver reset' to start over.")
            return 1

        # Mark as used and save (unless dry-run)
        if not args.dry_run:
            pick_and_mark(parsed, entry)
            save_state(parsed)

        # Display the selected entry
        print(f"🎯 {entry.content}")

        # Display metadata if present
        if entry.metadata:
            for key, value in entry.metadata.items():
                print(f"   {key}: {value}")

        if args.dry_run:
            print("\n   (Dry run - no changes made)")

        if args.verbose:
            available_count = len([e for e in parsed.entries if not e.is_used(history)])
            total_count = len(parsed.entries)
            print(f"\n   Remaining: {available_count}/{total_count}")

        return 0

    except FileNotFoundError:
        print(f"❌ File not found: {args.file}")
        return 1
    except ValueError as e:
        print(f"❌ {e}")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            raise
        return 1


def cmd_rollback(args) -> int:
    """
    Rollback the last selection.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        if args.dry_run:
            # Just show what would be rolled back
            parsed = parse_file(args.file)
            if not parsed.metadata.get('history'):
                print("ℹ️  No entries to rollback")
                return 0

            last_index = parsed.metadata['history'][-1]
            last_entry = find_entry_by_index(parsed, last_index)
            if last_entry:
                print(f"↩️  Would rollback: \"{last_entry.content}\"")
            else:
                print(f"↩️  Would rollback: index {last_index}")
            print("\n   (Dry run - no changes made)")
            return 0

        # Perform rollback
        entry = rollback_last(args.file)

        if entry is None:
            print("ℹ️  No entries to rollback")
            return 0

        print(f"↩️  Rolled back: \"{entry.content}\"")

        if args.verbose:
            parsed = parse_file(args.file)
            history = parsed.metadata.get('history', [])
            used_count = len(set(history))
            total_count = len(parsed.entries)
            print(f"   Status: {used_count}/{total_count} used")

        return 0

    except FileNotFoundError:
        print(f"❌ File not found: {args.file}")
        return 1
    except ValueError as e:
        print(f"❌ {e}")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            raise
        return 1


def cmd_reset(args) -> int:
    """
    Reset all entries to unused.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        if args.dry_run:
            # Just show what would be reset
            parsed = parse_file(args.file)
            history = parsed.metadata.get('history', [])
            used_count = len(set(history))
            total_count = len(parsed.entries)

            print(f"🔄 Would reset {used_count} of {total_count} entries")
            print("\n   (Dry run - no changes made)")
            return 0

        # Perform reset
        count = reset_all(args.file)

        if count == 0:
            print("ℹ️  All entries are already unused")
        else:
            print(f"🔄 Reset complete: {count} entries marked as unused")

        return 0

    except FileNotFoundError:
        print(f"❌ File not found: {args.file}")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            raise
        return 1


def cmd_status(args) -> int:
    """
    Show status information.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        parsed = parse_file(args.file)
        history = parsed.metadata.get('history', [])

        used_count = len(set(history))
        available_count = len([e for e in parsed.entries if not e.is_used(history)])
        total_count = len(parsed.entries)

        print(f"📊 Status: {used_count}/{total_count} entries used ({available_count} remaining)")

        if args.verbose:
            # Show history
            if history:
                print(f"\n   History ({len(history)} selections):")
                for i, idx in enumerate(reversed(history), 1):
                    entry = find_entry_by_index(parsed, idx)
                    if entry:
                        print(f"     {i}. {entry.content}")
                    else:
                        print(f"     {i}. [index {idx}]")
            else:
                print("\n   History: empty")

            # Show metadata columns (excluding "Used" if present)
            if parsed.headers:
                metadata_headers = [h for h in parsed.headers[1:] if h.lower() != 'used']
                if metadata_headers:
                    print(f"\n   Metadata columns: {', '.join(metadata_headers)}")

        return 0

    except FileNotFoundError:
        print(f"❌ File not found: {args.file}")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            raise
        return 1


def main(argv: Optional[list] = None) -> int:
    """
    Main entry point for the CLI.

    Args:
        argv: Command-line arguments (defaults to sys.argv)

    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(
        prog='quiver',
        description='A lightweight CLI tool for random selection from markdown tables',
        epilog='For more information, visit: https://github.com/valenc3x/quiver'
    )

    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )

    # Global options
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed output'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview action without making changes'
    )

    # Subcommands
    subparsers = parser.add_subparsers(
        dest='command',
        help='Command to execute',
        required=True
    )

    # Pick command
    pick_parser = subparsers.add_parser(
        'pick',
        help='Select a random unused entry'
    )
    pick_parser.add_argument(
        'file',
        help='Path to markdown file'
    )
    pick_parser.set_defaults(func=cmd_pick)

    # Rollback command
    rollback_parser = subparsers.add_parser(
        'rollback',
        help='Undo the last selection (LIFO)'
    )
    rollback_parser.add_argument(
        'file',
        help='Path to markdown file'
    )
    rollback_parser.set_defaults(func=cmd_rollback)

    # Reset command
    reset_parser = subparsers.add_parser(
        'reset',
        help='Mark all entries as unused'
    )
    reset_parser.add_argument(
        'file',
        help='Path to markdown file'
    )
    reset_parser.set_defaults(func=cmd_reset)

    # Status command
    status_parser = subparsers.add_parser(
        'status',
        help='Show usage statistics'
    )
    status_parser.add_argument(
        'file',
        help='Path to markdown file'
    )
    status_parser.set_defaults(func=cmd_status)

    # Parse arguments
    args = parser.parse_args(argv)

    # Execute command
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
