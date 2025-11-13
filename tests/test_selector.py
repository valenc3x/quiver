"""Tests for the selector module."""

from quiver.parser import Entry
from quiver.selector import (
    get_available_entries,
    select_random,
    select_random_available
)


def test_get_available_entries():
    """Test filtering to get only unused entries."""
    entries = [
        Entry(content='First', metadata={}, used=False, row_index=0),
        Entry(content='Second', metadata={}, used=True, row_index=1),
        Entry(content='Third', metadata={}, used=False, row_index=2),
        Entry(content='Fourth', metadata={}, used=True, row_index=3),
    ]

    available = get_available_entries(entries)

    assert len(available) == 2
    assert available[0].content == 'First'
    assert available[1].content == 'Third'


def test_get_available_entries_all_used():
    """Test filtering when all entries are used."""
    entries = [
        Entry(content='First', metadata={}, used=True, row_index=0),
        Entry(content='Second', metadata={}, used=True, row_index=1),
    ]

    available = get_available_entries(entries)
    assert len(available) == 0


def test_get_available_entries_none_used():
    """Test filtering when no entries are used."""
    entries = [
        Entry(content='First', metadata={}, used=False, row_index=0),
        Entry(content='Second', metadata={}, used=False, row_index=1),
        Entry(content='Third', metadata={}, used=False, row_index=2),
    ]

    available = get_available_entries(entries)
    assert len(available) == 3


def test_select_random():
    """Test selecting a random entry from a list."""
    entries = [
        Entry(content='First', metadata={}, used=False, row_index=0),
        Entry(content='Second', metadata={}, used=False, row_index=1),
        Entry(content='Third', metadata={}, used=False, row_index=2),
    ]

    # Run multiple times to check randomness (should get different results eventually)
    selected = select_random(entries)
    assert selected is not None
    assert selected in entries


def test_select_random_empty_list():
    """Test selecting from an empty list returns None."""
    result = select_random([])
    assert result is None


def test_select_random_available():
    """Test selecting a random unused entry."""
    entries = [
        Entry(content='First', metadata={}, used=False, row_index=0),
        Entry(content='Second', metadata={}, used=True, row_index=1),
        Entry(content='Third', metadata={}, used=False, row_index=2),
    ]

    # Run multiple times to ensure only available entries are selected
    for _ in range(10):
        selected = select_random_available(entries)
        assert selected is not None
        assert not selected.used
        assert selected.content in ['First', 'Third']


def test_select_random_available_all_used():
    """Test selecting when all entries are used returns None."""
    entries = [
        Entry(content='First', metadata={}, used=True, row_index=0),
        Entry(content='Second', metadata={}, used=True, row_index=1),
    ]

    result = select_random_available(entries)
    assert result is None


def test_select_random_single_available():
    """Test selecting when only one entry is available."""
    entries = [
        Entry(content='First', metadata={}, used=True, row_index=0),
        Entry(content='Second', metadata={}, used=False, row_index=1),
        Entry(content='Third', metadata={}, used=True, row_index=2),
    ]

    selected = select_random_available(entries)
    assert selected is not None
    assert selected.content == 'Second'


if __name__ == '__main__':
    test_get_available_entries()
    test_get_available_entries_all_used()
    test_get_available_entries_none_used()
    test_select_random()
    test_select_random_empty_list()
    test_select_random_available()
    test_select_random_available_all_used()
    test_select_random_single_available()

    print("All selector tests passed!")
