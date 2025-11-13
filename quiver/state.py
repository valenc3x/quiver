"""State management module for tracking entry usage."""

from typing import Optional

from .parser import Entry, ParsedFile, save_file


def mark_entry_used(parsed_file: ParsedFile, entry: Entry) -> None:
    """
    Mark an entry as used.

    Args:
        parsed_file: ParsedFile containing the entry
        entry: Entry to mark as used
    """
    entry.used = True


def mark_entry_unused(parsed_file: ParsedFile, entry: Entry) -> None:
    """
    Mark an entry as unused.

    Args:
        parsed_file: ParsedFile containing the entry
        entry: Entry to mark as unused
    """
    entry.used = False


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
    parsed_file.metadata['history'].append(entry.content)


def remove_from_history(parsed_file: ParsedFile) -> Optional[str]:
    """
    Remove the most recent entry from history (LIFO).

    Args:
        parsed_file: ParsedFile to update

    Returns:
        The content of the entry that was removed, or None if history is empty
    """
    if 'history' not in parsed_file.metadata or not parsed_file.metadata['history']:
        return None

    # Remove from the end (most recent)
    return parsed_file.metadata['history'].pop()


def find_entry_by_content(parsed_file: ParsedFile, content: str) -> Optional[Entry]:
    """
    Find an entry by its content string.

    Args:
        parsed_file: ParsedFile to search
        content: Content string to search for

    Returns:
        Entry with matching content, or None if not found
    """
    for entry in parsed_file.entries:
        if entry.content == content:
            return entry
    return None


def pick_and_mark(parsed_file: ParsedFile, entry: Entry) -> None:
    """
    Mark an entry as used and add it to history.

    Args:
        parsed_file: ParsedFile to update
        entry: Entry that was selected
    """
    mark_entry_used(parsed_file, entry)
    add_to_history(parsed_file, entry)


def save_state(parsed_file: ParsedFile) -> None:
    """
    Save the current state back to the file.

    Args:
        parsed_file: ParsedFile to save
    """
    save_file(parsed_file)
