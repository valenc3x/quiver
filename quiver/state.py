"""State management module for tracking entry usage."""

from typing import Optional

from .parser import Entry, ParsedFile, save_file


def add_to_history(parsed_file: ParsedFile, entry: Entry) -> None:
    """
    Add an entry to the selection history.

    Args:
        parsed_file: ParsedFile to update
        entry: Entry that was selected
    """
    if 'history' not in parsed_file.metadata:
        parsed_file.metadata['history'] = []

    # Add to the end of history (most recent)
    parsed_file.metadata['history'].append(entry.row_index)


def remove_from_history(parsed_file: ParsedFile) -> Optional[int]:
    """
    Remove the most recent entry from history (LIFO).

    Args:
        parsed_file: ParsedFile to update

    Returns:
        The index of the entry that was removed, or None if history is empty
    """
    if 'history' not in parsed_file.metadata or not parsed_file.metadata['history']:
        return None

    # Remove from the end (most recent)
    return parsed_file.metadata['history'].pop()


def find_entry_by_index(parsed_file: ParsedFile, index: int) -> Optional[Entry]:
    """
    Find an entry by its row index.

    Args:
        parsed_file: ParsedFile to search
        index: Row index to search for

    Returns:
        Entry with matching index, or None if not found
    """
    for entry in parsed_file.entries:
        if entry.row_index == index:
            return entry
    return None


def pick_and_mark(parsed_file: ParsedFile, entry: Entry) -> None:
    """
    Mark an entry as used by adding it to history.

    Args:
        parsed_file: ParsedFile to update
        entry: Entry that was selected
    """
    add_to_history(parsed_file, entry)


def save_state(parsed_file: ParsedFile) -> None:
    """
    Save the current state back to the file.

    Args:
        parsed_file: ParsedFile to save
    """
    save_file(parsed_file)


def validate_history(parsed_file: ParsedFile) -> None:
    """
    Validate and clean history by removing any invalid indices.

    This function gracefully handles table modifications by filtering out
    indices that are no longer valid (e.g., when rows are deleted or the
    table is reordered). Invalid indices are silently removed from history.

    Args:
        parsed_file: ParsedFile to validate and clean
    """
    if 'history' not in parsed_file.metadata:
        return

    history = parsed_file.metadata['history']
    num_entries = len(parsed_file.entries)

    # Filter out invalid indices (those that are out of bounds or negative)
    valid_history = [idx for idx in history if 0 <= idx < num_entries]

    # Update history with cleaned version
    parsed_file.metadata['history'] = valid_history
