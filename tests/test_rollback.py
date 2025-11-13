"""Tests for the rollback module."""

import tempfile
from pathlib import Path

from quiver.parser import parse_file
from quiver.rollback import rollback_last, reset_all
from quiver.state import pick_and_mark, save_state
from quiver.selector import select_random_available


def test_rollback_last_single():
    """Test rolling back a single selection."""
    content = """| Entry | Category | Used |
|-------|----------|------|
| First | Personal | [ ] |
| Second | Work | [ ] |
| Third | Personal | [ ] |
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
        assert parsed.entries[1].used is True
        assert parsed.metadata['history'] == ['Second']

        # Rollback
        rolled_back = rollback_last(temp_path)

        # Verify rollback
        assert rolled_back is not None
        assert rolled_back.content == 'Second'

        # Re-parse and verify state
        parsed = parse_file(temp_path)
        assert parsed.entries[1].used is False
        assert parsed.metadata['history'] == []

    finally:
        Path(temp_path).unlink()


def test_rollback_last_multiple():
    """Test rolling back multiple selections in LIFO order."""
    content = """| Entry | Used |
|-------|------|
| First | [ ] |
| Second | [ ] |
| Third | [ ] |
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

        # Verify all three are marked
        parsed = parse_file(temp_path)
        assert all(entry.used for entry in parsed.entries)
        assert parsed.metadata['history'] == ['First', 'Second', 'Third']

        # Rollback in LIFO order (Third, Second, First)
        rolled_back = rollback_last(temp_path)
        assert rolled_back.content == 'Third'

        parsed = parse_file(temp_path)
        assert not parsed.entries[2].used
        assert parsed.entries[0].used
        assert parsed.entries[1].used
        assert parsed.metadata['history'] == ['First', 'Second']

        rolled_back = rollback_last(temp_path)
        assert rolled_back.content == 'Second'

        parsed = parse_file(temp_path)
        assert not parsed.entries[1].used
        assert parsed.entries[0].used
        assert not parsed.entries[2].used
        assert parsed.metadata['history'] == ['First']

        rolled_back = rollback_last(temp_path)
        assert rolled_back.content == 'First'

        parsed = parse_file(temp_path)
        assert all(not entry.used for entry in parsed.entries)
        assert parsed.metadata['history'] == []

    finally:
        Path(temp_path).unlink()


def test_rollback_last_empty_history():
    """Test rolling back when history is empty returns None."""
    content = """| Entry | Used |
|-------|------|
| First | [ ] |
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        result = rollback_last(temp_path)
        assert result is None

    finally:
        Path(temp_path).unlink()


def test_rollback_last_inconsistent_state():
    """Test rollback when history entry doesn't match entries list."""
    content = """| Entry | Used |
|-------|------|
| First | [x] |

<!-- QUIVER_METADATA
history: ["Nonexistent Entry"]
-->
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        # This should raise ValueError
        try:
            rollback_last(temp_path)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert 'not in entries list' in str(e)

    finally:
        Path(temp_path).unlink()


def test_reset_all():
    """Test resetting all entries to unused."""
    content = """| Entry | Category | Used |
|-------|----------|------|
| First | Personal | [x] |
| Second | Work | [x] |
| Third | Personal | [ ] |
| Fourth | Work | [x] |
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        # Reset all
        count = reset_all(temp_path)

        # Should return count of entries that were used
        assert count == 3

        # Re-parse and verify
        parsed = parse_file(temp_path)

        # All entries should be unused
        assert all(not entry.used for entry in parsed.entries)

        # History should be empty
        assert parsed.metadata['history'] == []

    finally:
        Path(temp_path).unlink()


def test_reset_all_with_history():
    """Test that reset clears history as well."""
    content = """| Entry | Used |
|-------|------|
| First | [x] |
| Second | [x] |

<!-- QUIVER_METADATA
history: ["First", "Second"]
-->
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        # Reset
        reset_all(temp_path)

        # Re-parse and verify
        parsed = parse_file(temp_path)
        assert all(not entry.used for entry in parsed.entries)
        assert parsed.metadata['history'] == []

    finally:
        Path(temp_path).unlink()


def test_reset_all_already_unused():
    """Test resetting when all entries are already unused."""
    content = """| Entry | Used |
|-------|------|
| First | [ ] |
| Second | [ ] |
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        count = reset_all(temp_path)
        assert count == 0  # No entries were used

        # Verify file is unchanged (except maybe metadata)
        parsed = parse_file(temp_path)
        assert all(not entry.used for entry in parsed.entries)

    finally:
        Path(temp_path).unlink()


def test_full_workflow_with_rollback():
    """Test a complete workflow: pick -> pick -> rollback -> pick."""
    content = """# Test Workflow

| Entry | Category | Used |
|-------|----------|------|
| First | A | [ ] |
| Second | B | [ ] |
| Third | A | [ ] |
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        # Pick first entry
        parsed = parse_file(temp_path)
        entry1 = select_random_available(parsed.entries)
        assert entry1 is not None
        pick_and_mark(parsed, entry1)
        save_state(parsed)

        # Pick second entry
        parsed = parse_file(temp_path)
        entry2 = select_random_available(parsed.entries)
        assert entry2 is not None
        assert entry2.content != entry1.content  # Should be different
        pick_and_mark(parsed, entry2)
        save_state(parsed)

        # Verify two are used
        parsed = parse_file(temp_path)
        used_count = sum(1 for e in parsed.entries if e.used)
        assert used_count == 2

        # Rollback last pick
        rolled_back = rollback_last(temp_path)
        assert rolled_back.content == entry2.content

        # Verify only one is used now
        parsed = parse_file(temp_path)
        used_count = sum(1 for e in parsed.entries if e.used)
        assert used_count == 1

        # Pick another entry (should be able to pick the rolled-back one again)
        entry3 = select_random_available(parsed.entries)
        assert entry3 is not None
        pick_and_mark(parsed, entry3)
        save_state(parsed)

        # Verify two are used again
        parsed = parse_file(temp_path)
        used_count = sum(1 for e in parsed.entries if e.used)
        assert used_count == 2

    finally:
        Path(temp_path).unlink()


if __name__ == '__main__':
    test_rollback_last_single()
    test_rollback_last_multiple()
    test_rollback_last_empty_history()
    test_rollback_last_inconsistent_state()
    test_reset_all()
    test_reset_all_with_history()
    test_reset_all_already_unused()
    test_full_workflow_with_rollback()

    print("All rollback tests passed!")
