"""Tests for the state module."""

import tempfile
from pathlib import Path

from quiver.parser import Entry, ParsedFile, parse_file
from quiver.state import (
    mark_entry_used,
    mark_entry_unused,
    add_to_history,
    remove_from_history,
    find_entry_by_content,
    pick_and_mark,
    save_state
)


def test_mark_entry_used():
    """Test marking an entry as used."""
    entry = Entry(content='Test', metadata={}, used=False, row_index=0)
    parsed_file = ParsedFile(entries=[entry], headers=[], metadata={})

    mark_entry_used(parsed_file, entry)

    assert entry.used is True


def test_mark_entry_unused():
    """Test marking an entry as unused."""
    entry = Entry(content='Test', metadata={}, used=True, row_index=0)
    parsed_file = ParsedFile(entries=[entry], headers=[], metadata={})

    mark_entry_unused(parsed_file, entry)

    assert entry.used is False


def test_add_to_history():
    """Test adding entries to history."""
    entry1 = Entry(content='First', metadata={}, used=False, row_index=0)
    entry2 = Entry(content='Second', metadata={}, used=False, row_index=1)

    parsed_file = ParsedFile(
        entries=[entry1, entry2],
        headers=[],
        metadata={'history': []}
    )

    add_to_history(parsed_file, entry1)
    assert parsed_file.metadata['history'] == ['First']

    add_to_history(parsed_file, entry2)
    assert parsed_file.metadata['history'] == ['First', 'Second']


def test_add_to_history_no_existing_history():
    """Test adding to history when history doesn't exist."""
    entry = Entry(content='Test', metadata={}, used=False, row_index=0)
    parsed_file = ParsedFile(entries=[entry], headers=[], metadata={})

    add_to_history(parsed_file, entry)

    assert 'history' in parsed_file.metadata
    assert parsed_file.metadata['history'] == ['Test']


def test_remove_from_history():
    """Test removing from history (LIFO)."""
    parsed_file = ParsedFile(
        entries=[],
        headers=[],
        metadata={'history': ['First', 'Second', 'Third']}
    )

    # Remove most recent (Third)
    removed = remove_from_history(parsed_file)
    assert removed == 'Third'
    assert parsed_file.metadata['history'] == ['First', 'Second']

    # Remove next most recent (Second)
    removed = remove_from_history(parsed_file)
    assert removed == 'Second'
    assert parsed_file.metadata['history'] == ['First']


def test_remove_from_history_empty():
    """Test removing from empty history returns None."""
    parsed_file = ParsedFile(
        entries=[],
        headers=[],
        metadata={'history': []}
    )

    removed = remove_from_history(parsed_file)
    assert removed is None


def test_remove_from_history_no_history():
    """Test removing when history doesn't exist returns None."""
    parsed_file = ParsedFile(entries=[], headers=[], metadata={})

    removed = remove_from_history(parsed_file)
    assert removed is None


def test_find_entry_by_content():
    """Test finding an entry by its content."""
    entries = [
        Entry(content='First', metadata={}, used=False, row_index=0),
        Entry(content='Second', metadata={}, used=False, row_index=1),
        Entry(content='Third', metadata={}, used=False, row_index=2),
    ]

    parsed_file = ParsedFile(entries=entries, headers=[], metadata={})

    # Find existing entry
    found = find_entry_by_content(parsed_file, 'Second')
    assert found is not None
    assert found.content == 'Second'
    assert found.row_index == 1

    # Find non-existing entry
    not_found = find_entry_by_content(parsed_file, 'Nonexistent')
    assert not_found is None


def test_pick_and_mark():
    """Test picking an entry marks it and adds to history."""
    entry = Entry(content='Test entry', metadata={}, used=False, row_index=0)
    parsed_file = ParsedFile(
        entries=[entry],
        headers=[],
        metadata={'history': []}
    )

    pick_and_mark(parsed_file, entry)

    # Check entry is marked as used
    assert entry.used is True

    # Check entry is in history
    assert 'Test entry' in parsed_file.metadata['history']


def test_save_state():
    """Test saving state to file."""
    content = """| Entry | Category | Used |
|-------|----------|------|
| First | Personal | [ ] |
| Second | Work | [ ] |
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        # Parse the file
        parsed = parse_file(temp_path)

        # Modify state
        mark_entry_used(parsed, parsed.entries[0])
        add_to_history(parsed, parsed.entries[0])

        # Save state
        save_state(parsed)

        # Re-parse and verify changes persisted
        parsed2 = parse_file(temp_path)

        assert parsed2.entries[0].used is True
        assert parsed2.entries[1].used is False
        assert parsed2.metadata['history'] == ['First']

    finally:
        Path(temp_path).unlink()


def test_full_workflow():
    """Test a complete pick -> mark -> save workflow."""
    content = """# Test List

| Entry | Category | Used |
|-------|----------|------|
| First entry | Personal | [ ] |
| Second entry | Work | [ ] |
| Third entry | Personal | [ ] |
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        # Parse the file
        parsed = parse_file(temp_path)

        # Pick an entry
        entry_to_pick = parsed.entries[1]  # Pick "Second entry"

        # Mark it as used and add to history
        pick_and_mark(parsed, entry_to_pick)

        # Save
        save_state(parsed)

        # Re-parse
        parsed2 = parse_file(temp_path)

        # Verify
        assert parsed2.entries[0].used is False
        assert parsed2.entries[1].used is True  # Marked as used
        assert parsed2.entries[2].used is False
        assert parsed2.metadata['history'] == ['Second entry']

    finally:
        Path(temp_path).unlink()


if __name__ == '__main__':
    test_mark_entry_used()
    test_mark_entry_unused()
    test_add_to_history()
    test_add_to_history_no_existing_history()
    test_remove_from_history()
    test_remove_from_history_empty()
    test_remove_from_history_no_history()
    test_find_entry_by_content()
    test_pick_and_mark()
    test_save_state()
    test_full_workflow()

    print("All state tests passed!")
