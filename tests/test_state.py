"""Tests for the state module."""

import tempfile
from pathlib import Path

from quiver.parser import Entry, ParsedFile, parse_file
from quiver.state import (
    add_to_history,
    remove_from_history,
    find_entry_by_index,
    pick_and_mark,
    save_state,
    validate_history
)


def test_add_to_history():
    """Test adding entries to history."""
    entry1 = Entry(content='First', metadata={}, row_index=0)
    entry2 = Entry(content='Second', metadata={}, row_index=1)

    parsed_file = ParsedFile(
        entries=[entry1, entry2],
        headers=[],
        metadata={'history': []}
    )

    add_to_history(parsed_file, entry1)
    assert parsed_file.metadata['history'] == [0]

    add_to_history(parsed_file, entry2)
    assert parsed_file.metadata['history'] == [0, 1]


def test_add_to_history_no_existing_history():
    """Test adding to history when history doesn't exist."""
    entry = Entry(content='Test', metadata={}, row_index=0)
    parsed_file = ParsedFile(entries=[entry], headers=[], metadata={})

    add_to_history(parsed_file, entry)

    assert 'history' in parsed_file.metadata
    assert parsed_file.metadata['history'] == [0]


def test_remove_from_history():
    """Test removing from history (LIFO)."""
    parsed_file = ParsedFile(
        entries=[],
        headers=[],
        metadata={'history': [0, 1, 2]}
    )

    # Remove most recent (2)
    removed = remove_from_history(parsed_file)
    assert removed == 2
    assert parsed_file.metadata['history'] == [0, 1]

    # Remove next most recent (1)
    removed = remove_from_history(parsed_file)
    assert removed == 1
    assert parsed_file.metadata['history'] == [0]


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


def test_find_entry_by_index():
    """Test finding an entry by its row index."""
    entries = [
        Entry(content='First', metadata={}, row_index=0),
        Entry(content='Second', metadata={}, row_index=1),
        Entry(content='Third', metadata={}, row_index=2),
    ]

    parsed_file = ParsedFile(entries=entries, headers=[], metadata={})

    # Find existing entry
    found = find_entry_by_index(parsed_file, 1)
    assert found is not None
    assert found.content == 'Second'
    assert found.row_index == 1

    # Find non-existing entry
    not_found = find_entry_by_index(parsed_file, 99)
    assert not_found is None


def test_pick_and_mark():
    """Test picking an entry adds it to history."""
    entry = Entry(content='Test entry', metadata={}, row_index=0)
    parsed_file = ParsedFile(
        entries=[entry],
        headers=[],
        metadata={'history': []}
    )

    pick_and_mark(parsed_file, entry)

    # Check entry is in history
    assert 0 in parsed_file.metadata['history']


def test_save_state():
    """Test saving state to file."""
    content = """| Entry | Category |
|-------|----------|
| First | Personal |
| Second | Work |

<!-- QUIVER_METADATA
history: []
-->
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        # Parse the file
        parsed = parse_file(temp_path)

        # Modify state
        add_to_history(parsed, parsed.entries[0])

        # Save state
        save_state(parsed)

        # Re-parse and verify changes persisted
        parsed2 = parse_file(temp_path)
        history = parsed2.metadata.get('history', [])

        assert parsed2.entries[0].is_used(history) is True
        assert parsed2.entries[1].is_used(history) is False
        assert parsed2.metadata['history'] == [0]

    finally:
        Path(temp_path).unlink()


def test_validate_history_valid():
    """Test validation passes with valid indices."""
    entries = [
        Entry(content='First', metadata={}, row_index=0),
        Entry(content='Second', metadata={}, row_index=1),
        Entry(content='Third', metadata={}, row_index=2),
    ]
    parsed_file = ParsedFile(
        entries=entries,
        headers=[],
        metadata={'history': [0, 2, 1]}
    )

    # Should not raise
    validate_history(parsed_file)


def test_validate_history_out_of_bounds():
    """Test validation fails with out-of-bounds indices."""
    entries = [
        Entry(content='First', metadata={}, row_index=0),
        Entry(content='Second', metadata={}, row_index=1),
    ]
    parsed_file = ParsedFile(
        entries=entries,
        headers=[],
        metadata={'history': [0, 1, 5]}  # 5 is out of bounds
    )

    try:
        validate_history(parsed_file)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert 'invalid index' in str(e)
        assert 'quiver reset' in str(e).lower()


def test_full_workflow():
    """Test a complete pick -> mark -> save workflow."""
    content = """# Test List

| Entry | Category |
|-------|----------|
| First entry | Personal |
| Second entry | Work |
| Third entry | Personal |

<!-- QUIVER_METADATA
history: []
-->
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
        history = parsed2.metadata.get('history', [])

        # Verify
        assert parsed2.entries[0].is_used(history) is False
        assert parsed2.entries[1].is_used(history) is True  # Marked as used
        assert parsed2.entries[2].is_used(history) is False
        assert parsed2.metadata['history'] == [1]

    finally:
        Path(temp_path).unlink()


if __name__ == '__main__':
    test_add_to_history()
    test_add_to_history_no_existing_history()
    test_remove_from_history()
    test_remove_from_history_empty()
    test_remove_from_history_no_history()
    test_find_entry_by_index()
    test_pick_and_mark()
    test_save_state()
    test_validate_history_valid()
    test_validate_history_out_of_bounds()
    test_full_workflow()

    print("All state tests passed!")
