"""Rollback module for undoing selections."""

from typing import Optional

from .parser import Entry, ParsedFile, parse_file, save_file
from .state import find_entry_by_content, mark_entry_unused, remove_from_history


def rollback_last(filepath: str) -> Optional[Entry]:
    """
    Rollback the last selected entry (LIFO).

    This function:
    1. Loads the file
    2. Gets the most recent entry from history
    3. Finds that entry in the entries list
    4. Marks it as unused
    5. Removes it from history
    6. Saves the file

    Args:
        filepath: Path to the markdown file

    Returns:
        The Entry that was rolled back, or None if history is empty

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If the entry in history is not found in the entries list
    """
    # Parse the file
    parsed = parse_file(filepath)

    # Get the most recent entry from history
    last_content = remove_from_history(parsed)

    if last_content is None:
        return None

    # Find the entry
    entry = find_entry_by_content(parsed, last_content)

    if entry is None:
        # This shouldn't happen if data is consistent
        raise ValueError(
            f"Entry '{last_content}' found in history but not in entries list"
        )

    # Mark as unused
    mark_entry_unused(parsed, entry)

    # Save the file
    save_file(parsed)

    return entry


def reset_all(filepath: str) -> int:
    """
    Reset all entries to unused state and clear history.

    Args:
        filepath: Path to the markdown file

    Returns:
        Number of entries that were reset

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    # Parse the file
    parsed = parse_file(filepath)

    # Count how many were used
    reset_count = sum(1 for entry in parsed.entries if entry.used)

    # Mark all entries as unused
    for entry in parsed.entries:
        mark_entry_unused(parsed, entry)

    # Clear history
    parsed.metadata['history'] = []

    # Save the file
    save_file(parsed)

    return reset_count
