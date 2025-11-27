"""Rollback module for undoing selections."""

from typing import Optional

from .parser import Entry, ParsedFile, parse_file, save_file
from .state import find_entry_by_index, remove_from_history, validate_history


def rollback_last(filepath: str) -> Optional[Entry]:
    """
    Rollback the last selected entry (LIFO).

    This function:
    1. Loads the file
    2. Validates history indices
    3. Gets the most recent entry index from history
    4. Finds that entry in the entries list
    5. Removes it from history (already done by remove_from_history)
    6. Saves the file

    Args:
        filepath: Path to the markdown file

    Returns:
        The Entry that was rolled back, or None if history is empty

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If the entry index in history is not found in the entries list
    """
    # Parse the file
    parsed = parse_file(filepath)

    # Validate history
    validate_history(parsed)

    # Get the most recent entry index from history
    last_index = remove_from_history(parsed)

    if last_index is None:
        return None

    # Find the entry
    entry = find_entry_by_index(parsed, last_index)

    if entry is None:
        # This shouldn't happen if data is consistent
        raise ValueError(
            f"Entry index {last_index} found in history but not in entries list"
        )

    # Save the file (entry is already removed from history)
    save_file(parsed)

    return entry


def reset_all(filepath: str) -> int:
    """
    Reset all entries to unused state by clearing history.

    Args:
        filepath: Path to the markdown file

    Returns:
        Number of entries that were reset

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    # Parse the file
    parsed = parse_file(filepath)

    # Count how many were used (unique indices in history)
    reset_count = len(set(parsed.metadata.get('history', [])))

    # Clear history
    parsed.metadata['history'] = []

    # Save the file
    save_file(parsed)

    return reset_count
