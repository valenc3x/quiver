"""Tests for the rollback module."""

import tempfile
from pathlib import Path

from quiver.parser import parse_file
from quiver.rollback import rollback_last, reset_all
from quiver.state import pick_and_mark, save_state
from quiver.selector import select_random_available


def test_rollback_last_single():
    """Test rolling back a single selection."""
    content = """| Entry | Category |
|-------|----------|
| First | Personal |
| Second | Work |
| Third | Personal |

<!-- QUIVER_METADATA
history: []
-->
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        # Parse and pick an entry
        parsed = parse_file(temp_path)
        entry = parsed.entries[1]  # Pick "Second"
        pick_and_mark(parsed, entry)
        save_state(parsed)

        # Verify it's marked as used
        parsed = parse_file(temp_path)
        history = parsed.metadata.get('history', [])
        assert parsed.entries[1].is_used(history) is True
        assert parsed.metadata['history'] == [1]

        # Rollback
        rolled_back = rollback_last(temp_path)

        # Verify rollback
        assert rolled_back is not None
        assert rolled_back.content == 'Second'

        # Re-parse and verify state
        parsed = parse_file(temp_path)
        history = parsed.metadata.get('history', [])
        assert parsed.entries[1].is_used(history) is False
        assert parsed.metadata['history'] == []

    finally:
        Path(temp_path).unlink()


def test_rollback_last_multiple():
    """Test rolling back multiple selections in LIFO order."""
    content = """| Entry |
|-------|
| First |
| Second |
| Third |

<!-- QUIVER_METADATA
history: []
-->
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        # Pick three entries in sequence
        for i in range(3):
            parsed = parse_file(temp_path)
            entry = parsed.entries[i]
            pick_and_mark(parsed, entry)
            save_state(parsed)

        # Verify all three are in history
        parsed = parse_file(temp_path)
        history = parsed.metadata.get('history', [])
        assert all(entry.is_used(history) for entry in parsed.entries)
        assert parsed.metadata['history'] == [0, 1, 2]

        # Rollback in LIFO order (Third, Second, First)
        rolled_back = rollback_last(temp_path)
        assert rolled_back.content == 'Third'

        parsed = parse_file(temp_path)
        history = parsed.metadata.get('history', [])
        assert not parsed.entries[2].is_used(history)
        assert parsed.entries[0].is_used(history)
        assert parsed.entries[1].is_used(history)
        assert parsed.metadata['history'] == [0, 1]

        rolled_back = rollback_last(temp_path)
        assert rolled_back.content == 'Second'

        parsed = parse_file(temp_path)
        history = parsed.metadata.get('history', [])
        assert not parsed.entries[1].is_used(history)
        assert parsed.entries[0].is_used(history)
        assert not parsed.entries[2].is_used(history)
        assert parsed.metadata['history'] == [0]

        rolled_back = rollback_last(temp_path)
        assert rolled_back.content == 'First'

        parsed = parse_file(temp_path)
        history = parsed.metadata.get('history', [])
        assert all(not entry.is_used(history) for entry in parsed.entries)
        assert parsed.metadata['history'] == []

    finally:
        Path(temp_path).unlink()


def test_rollback_last_empty_history():
    """Test rolling back when history is empty returns None."""
    content = """| Entry |
|-------|
| First |

<!-- QUIVER_METADATA
history: []
-->
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        result = rollback_last(temp_path)
        assert result is None

    finally:
        Path(temp_path).unlink()


def test_rollback_last_invalid_index():
    """Test rollback when history contains invalid index."""
    content = """| Entry |
|-------|
| First |

<!-- QUIVER_METADATA
history: [5]
-->
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        # This should raise ValueError due to validation
        try:
            rollback_last(temp_path)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert 'invalid index' in str(e)

    finally:
        Path(temp_path).unlink()


def test_reset_all():
    """Test resetting all entries to unused."""
    content = """| Entry | Category |
|-------|----------|
| First | Personal |
| Second | Work |
| Third | Personal |
| Fourth | Work |

<!-- QUIVER_METADATA
history: [0, 1, 3]
-->
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        # Reset all
        count = reset_all(temp_path)

        # Should return count of unique entries that were used
        assert count == 3

        # Re-parse and verify
        parsed = parse_file(temp_path)
        history = parsed.metadata.get('history', [])

        # All entries should be unused
        assert all(not entry.is_used(history) for entry in parsed.entries)

        # History should be empty
        assert parsed.metadata['history'] == []

    finally:
        Path(temp_path).unlink()


def test_reset_all_with_duplicates_in_history():
    """Test that reset counts unique entries (handles duplicate indices)."""
    content = """| Entry |
|-------|
| First |
| Second |

<!-- QUIVER_METADATA
history: [0, 1, 0, 1, 0]
-->
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        # Reset
        count = reset_all(temp_path)

        # Should count unique indices (0 and 1)
        assert count == 2

        # Re-parse and verify
        parsed = parse_file(temp_path)
        history = parsed.metadata.get('history', [])
        assert all(not entry.is_used(history) for entry in parsed.entries)
        assert parsed.metadata['history'] == []

    finally:
        Path(temp_path).unlink()


def test_reset_all_already_unused():
    """Test resetting when all entries are already unused."""
    content = """| Entry |
|-------|
| First |
| Second |

<!-- QUIVER_METADATA
history: []
-->
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        count = reset_all(temp_path)
        assert count == 0  # No entries were used

        # Verify file is unchanged (except maybe metadata)
        parsed = parse_file(temp_path)
        history = parsed.metadata.get('history', [])
        assert all(not entry.is_used(history) for entry in parsed.entries)

    finally:
        Path(temp_path).unlink()


def test_full_workflow_with_rollback():
    """Test a complete workflow: pick -> pick -> rollback -> pick."""
    content = """# Test Workflow

| Entry | Category |
|-------|----------|
| First | A |
| Second | B |
| Third | A |

<!-- QUIVER_METADATA
history: []
-->
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        # Pick first entry
        parsed = parse_file(temp_path)
        history = parsed.metadata.get('history', [])
        entry1 = select_random_available(parsed.entries, history)
        assert entry1 is not None
        pick_and_mark(parsed, entry1)
        save_state(parsed)

        # Pick second entry
        parsed = parse_file(temp_path)
        history = parsed.metadata.get('history', [])
        entry2 = select_random_available(parsed.entries, history)
        assert entry2 is not None
        assert entry2.content != entry1.content  # Should be different
        pick_and_mark(parsed, entry2)
        save_state(parsed)

        # Verify two are used
        parsed = parse_file(temp_path)
        history = parsed.metadata.get('history', [])
        used_count = sum(1 for idx in set(history) if idx < len(parsed.entries))
        assert used_count == 2

        # Rollback last pick
        rolled_back = rollback_last(temp_path)
        assert rolled_back.content == entry2.content

        # Verify only one is used now
        parsed = parse_file(temp_path)
        history = parsed.metadata.get('history', [])
        used_count = sum(1 for idx in set(history) if idx < len(parsed.entries))
        assert used_count == 1

        # Pick another entry (should be able to pick the rolled-back one again)
        entry3 = select_random_available(parsed.entries, history)
        assert entry3 is not None
        pick_and_mark(parsed, entry3)
        save_state(parsed)

        # Verify two are used again
        parsed = parse_file(temp_path)
        history = parsed.metadata.get('history', [])
        used_count = sum(1 for idx in set(history) if idx < len(parsed.entries))
        assert used_count == 2

    finally:
        Path(temp_path).unlink()


if __name__ == '__main__':
    test_rollback_last_single()
    test_rollback_last_multiple()
    test_rollback_last_empty_history()
    test_rollback_last_invalid_index()
    test_reset_all()
    test_reset_all_with_duplicates_in_history()
    test_reset_all_already_unused()
    test_full_workflow_with_rollback()

    print("All rollback tests passed!")
