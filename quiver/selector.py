"""Selector module for random entry selection."""

import random
from typing import List, Optional

from .parser import Entry


def get_available_entries(entries: List[Entry]) -> List[Entry]:
    """
    Filter entries to only include unused ones.

    Args:
        entries: List of Entry objects

    Returns:
        List of Entry objects where used=False
    """
    return [entry for entry in entries if not entry.used]


def select_random(entries: List[Entry]) -> Optional[Entry]:
    """
    Select a random entry from the list.

    Args:
        entries: List of Entry objects to choose from

    Returns:
        Randomly selected Entry, or None if list is empty
    """
    if not entries:
        return None

    return random.choice(entries)


def select_random_available(entries: List[Entry]) -> Optional[Entry]:
    """
    Select a random unused entry from the list.

    Args:
        entries: List of Entry objects

    Returns:
        Randomly selected unused Entry, or None if no unused entries
    """
    available = get_available_entries(entries)
    return select_random(available)
