"""Integration tests for the CLI."""

import tempfile
from pathlib import Path
from io import StringIO
import sys

from quiver.cli import main


def capture_output(func, *args):
    """Capture stdout output from a function."""
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        result = func(*args)
        output = sys.stdout.getvalue()
        return result, output
    finally:
        sys.stdout = old_stdout


def test_cli_pick():
    """Test the pick command."""
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
        # Run pick command
        exit_code, output = capture_output(main, ['pick', temp_path])

        assert exit_code == 0
        assert '🎯' in output
        assert 'Category:' in output

        # Verify one entry is now used
        from quiver.parser import parse_file
        parsed = parse_file(temp_path)
        used_count = sum(1 for e in parsed.entries if e.used)
        assert used_count == 1

    finally:
        Path(temp_path).unlink()


def test_cli_pick_all_used():
    """Test pick when all entries are used."""
    content = """| Entry | Used |
|-------|------|
| First | [x] |
| Second | [x] |
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        exit_code, output = capture_output(main, ['pick', temp_path])

        assert exit_code == 1
        assert 'No unused entries' in output

    finally:
        Path(temp_path).unlink()


def test_cli_pick_dry_run():
    """Test pick with --dry-run flag."""
    content = """| Entry | Used |
|-------|------|
| First | [ ] |
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        exit_code, output = capture_output(main, ['--dry-run', 'pick', temp_path])

        assert exit_code == 0
        assert 'Dry run' in output

        # Verify no changes were made
        from quiver.parser import parse_file
        parsed = parse_file(temp_path)
        assert all(not e.used for e in parsed.entries)

    finally:
        Path(temp_path).unlink()


def test_cli_rollback():
    """Test the rollback command."""
    content = """| Entry | Used |
|-------|------|
| First | [x] |

<!-- QUIVER_METADATA
history: ["First"]
-->
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        exit_code, output = capture_output(main, ['rollback', temp_path])

        assert exit_code == 0
        assert 'Rolled back' in output
        assert 'First' in output

        # Verify entry is now unused
        from quiver.parser import parse_file
        parsed = parse_file(temp_path)
        assert all(not e.used for e in parsed.entries)
        assert parsed.metadata['history'] == []

    finally:
        Path(temp_path).unlink()


def test_cli_rollback_empty():
    """Test rollback when history is empty."""
    content = """| Entry | Used |
|-------|------|
| First | [ ] |
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        exit_code, output = capture_output(main, ['rollback', temp_path])

        assert exit_code == 0
        assert 'No entries to rollback' in output

    finally:
        Path(temp_path).unlink()


def test_cli_reset():
    """Test the reset command."""
    content = """| Entry | Used |
|-------|------|
| First | [x] |
| Second | [x] |
| Third | [ ] |
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        exit_code, output = capture_output(main, ['reset', temp_path])

        assert exit_code == 0
        assert 'Reset complete' in output
        assert '2 entries' in output

        # Verify all entries are now unused
        from quiver.parser import parse_file
        parsed = parse_file(temp_path)
        assert all(not e.used for e in parsed.entries)

    finally:
        Path(temp_path).unlink()


def test_cli_reset_already_unused():
    """Test reset when all entries are already unused."""
    content = """| Entry | Used |
|-------|------|
| First | [ ] |
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        exit_code, output = capture_output(main, ['reset', temp_path])

        assert exit_code == 0
        assert 'already unused' in output

    finally:
        Path(temp_path).unlink()


def test_cli_status():
    """Test the status command."""
    content = """| Entry | Category | Used |
|-------|----------|------|
| First | Personal | [x] |
| Second | Work | [ ] |
| Third | Personal | [ ] |
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        exit_code, output = capture_output(main, ['status', temp_path])

        assert exit_code == 0
        assert '📊 Status' in output
        assert '1/3' in output
        assert '2 remaining' in output

    finally:
        Path(temp_path).unlink()


def test_cli_status_verbose():
    """Test status with verbose flag."""
    content = """| Entry | Category | Used |
|-------|----------|------|
| First | Personal | [x] |
| Second | Work | [x] |

<!-- QUIVER_METADATA
history: ["First", "Second"]
-->
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        exit_code, output = capture_output(main, ['--verbose', 'status', temp_path])

        assert exit_code == 0
        assert 'History' in output
        assert 'Category' in output  # Metadata columns

    finally:
        Path(temp_path).unlink()


def test_cli_file_not_found():
    """Test handling of non-existent file."""
    exit_code, output = capture_output(main, ['pick', '/nonexistent/file.md'])

    assert exit_code == 1
    assert 'not found' in output.lower()


def test_cli_version():
    """Test --version flag."""
    try:
        exit_code, output = capture_output(main, ['--version'])
    except SystemExit as e:
        # argparse --version calls sys.exit(0)
        assert e.code == 0


def test_cli_full_workflow():
    """Test a complete workflow: pick -> status -> rollback -> reset."""
    content = """| Entry | Category | Used |
|-------|----------|------|
| First | A | [ ] |
| Second | B | [ ] |
| Third | A | [ ] |
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        # Pick an entry
        exit_code, output = capture_output(main, ['pick', temp_path])
        assert exit_code == 0
        assert '🎯' in output

        # Check status
        exit_code, output = capture_output(main, ['status', temp_path])
        assert exit_code == 0
        assert '1/3' in output

        # Pick another
        exit_code, output = capture_output(main, ['pick', temp_path])
        assert exit_code == 0

        # Check status
        exit_code, output = capture_output(main, ['status', temp_path])
        assert exit_code == 0
        assert '2/3' in output

        # Rollback one
        exit_code, output = capture_output(main, ['rollback', temp_path])
        assert exit_code == 0

        # Check status
        exit_code, output = capture_output(main, ['status', temp_path])
        assert exit_code == 0
        assert '1/3' in output

        # Reset all
        exit_code, output = capture_output(main, ['reset', temp_path])
        assert exit_code == 0

        # Check status
        exit_code, output = capture_output(main, ['status', temp_path])
        assert exit_code == 0
        assert '0/3' in output

    finally:
        Path(temp_path).unlink()


if __name__ == '__main__':
    test_cli_pick()
    test_cli_pick_all_used()
    test_cli_pick_dry_run()
    test_cli_rollback()
    test_cli_rollback_empty()
    test_cli_reset()
    test_cli_reset_already_unused()
    test_cli_status()
    test_cli_status_verbose()
    test_cli_file_not_found()
    test_cli_full_workflow()

    print("All CLI tests passed!")
