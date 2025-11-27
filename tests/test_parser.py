"""Tests for the parser module."""

import tempfile
from pathlib import Path

from quiver.parser import (
    Entry,
    ParsedFile,
    MarkdownTableParser,
    parse_file,
    save_file
)


def test_parse_simple_table():
    """Test parsing a simple markdown table."""
    content = """# Test Table

| Entry | Category |
|-------|----------|
| First entry | Personal |
| Second entry | Work |
| Third entry | Personal |

<!-- QUIVER_METADATA
history: [1]
-->
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        parsed = parse_file(temp_path)

        # Check headers
        assert parsed.headers == ['Entry', 'Category']

        # Check entries
        assert len(parsed.entries) == 3

        # Check history
        history = parsed.metadata.get('history', [])
        assert history == [1]

        # First entry
        assert parsed.entries[0].content == 'First entry'
        assert parsed.entries[0].metadata == {'Category': 'Personal'}
        assert parsed.entries[0].is_used(history) is False

        # Second entry (marked as used in history)
        assert parsed.entries[1].content == 'Second entry'
        assert parsed.entries[1].metadata == {'Category': 'Work'}
        assert parsed.entries[1].is_used(history) is True

        # Third entry
        assert parsed.entries[2].content == 'Third entry'
        assert parsed.entries[2].metadata == {'Category': 'Personal'}
        assert parsed.entries[2].is_used(history) is False

    finally:
        Path(temp_path).unlink()


def test_parse_table_with_multiple_metadata_columns():
    """Test parsing a table with multiple metadata columns."""
    content = """| Restaurant | Cuisine | Price |
|------------|---------|-------|
| Mario's Pizza | Italian | $$ |
| Sushi House | Japanese | $$$ |

<!-- QUIVER_METADATA
history: [1]
-->
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        parsed = parse_file(temp_path)

        assert len(parsed.entries) == 2
        history = parsed.metadata.get('history', [])

        # First entry
        assert parsed.entries[0].content == "Mario's Pizza"
        assert parsed.entries[0].metadata == {
            'Cuisine': 'Italian',
            'Price': '$$'
        }
        assert parsed.entries[0].is_used(history) is False

        # Second entry
        assert parsed.entries[1].content == 'Sushi House'
        assert parsed.entries[1].metadata == {
            'Cuisine': 'Japanese',
            'Price': '$$$'
        }
        assert parsed.entries[1].is_used(history) is True

    finally:
        Path(temp_path).unlink()


def test_parse_table_with_metadata():
    """Test parsing a table with QUIVER_METADATA."""
    content = """| Entry | Category |
|-------|----------|
| First entry | Personal |
| Second entry | Work |

<!-- QUIVER_METADATA
history: [0]
-->
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        parsed = parse_file(temp_path)

        assert len(parsed.entries) == 2
        assert parsed.metadata['history'] == [0]

    finally:
        Path(temp_path).unlink()


def test_serialize_file():
    """Test serializing a ParsedFile back to markdown."""
    # Create a parsed file
    entries = [
        Entry(
            content='First entry',
            metadata={'Category': 'Personal'},
            row_index=0
        ),
        Entry(
            content='Second entry',
            metadata={'Category': 'Work'},
            row_index=1
        )
    ]

    parsed = ParsedFile(
        entries=entries,
        headers=['Entry', 'Category'],
        metadata={'history': [1]},
        raw_content='',
        filepath=''
    )

    # Serialize
    result = MarkdownTableParser.serialize_file(parsed)

    # Check that it contains expected parts
    assert '| Entry | Category |' in result
    assert '| First entry | Personal |' in result
    assert '| Second entry | Work |' in result
    assert '<!-- QUIVER_METADATA' in result
    assert 'history: [1]' in result
    # Should NOT contain Used column
    assert 'Used' not in result


def test_round_trip():
    """Test parsing and serializing maintains data integrity."""
    original_content = """# My List

| Entry | Category |
|-------|----------|
| First entry | Personal |
| Second entry | Work |

<!-- QUIVER_METADATA
history: [1]
-->
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(original_content)
        temp_path = f.name

    try:
        # Parse
        parsed = parse_file(temp_path)

        # Verify parsed data
        assert len(parsed.entries) == 2
        assert parsed.entries[0].content == 'First entry'
        history = parsed.metadata.get('history', [])
        assert parsed.entries[0].is_used(history) is False
        assert parsed.entries[1].content == 'Second entry'
        assert parsed.entries[1].is_used(history) is True
        assert parsed.metadata['history'] == [1]

        # Modify history (mark first entry as used too)
        parsed.metadata['history'].insert(0, 0)

        # Save back
        save_file(parsed)

        # Re-parse
        parsed2 = parse_file(temp_path)
        history2 = parsed2.metadata.get('history', [])

        # Verify changes persisted
        assert parsed2.entries[0].is_used(history2) is True
        assert parsed2.entries[1].is_used(history2) is True
        assert parsed2.metadata['history'] == [0, 1]

    finally:
        Path(temp_path).unlink()


def test_parse_empty_metadata():
    """Test parsing a file with empty QUIVER_METADATA."""
    content = """| Entry | Category |
|-------|----------|
| Test | Personal |

<!-- QUIVER_METADATA
history: []
-->
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        parsed = parse_file(temp_path)
        assert parsed.metadata['history'] == []

    finally:
        Path(temp_path).unlink()


def test_parse_no_metadata():
    """Test parsing a file without QUIVER_METADATA."""
    content = """| Entry | Category |
|-------|----------|
| Test | Personal |
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        parsed = parse_file(temp_path)
        assert parsed.metadata['history'] == []

    finally:
        Path(temp_path).unlink()


def test_parse_file_not_found():
    """Test parsing a non-existent file raises FileNotFoundError."""
    try:
        parse_file('/nonexistent/file.md')
        assert False, "Should have raised FileNotFoundError"
    except FileNotFoundError as e:
        assert 'not found' in str(e).lower()


def test_parse_real_examples():
    """Test parsing the actual example files."""
    # Get the examples directory
    examples_dir = Path(__file__).parent.parent / 'examples'

    if examples_dir.exists():
        # Test prompts.md
        prompts_file = examples_dir / 'prompts.md'
        if prompts_file.exists():
            parsed = parse_file(str(prompts_file))
            assert len(parsed.entries) > 0
            assert 'Category' in parsed.headers
            history = parsed.metadata.get('history', [])
            assert all(not entry.is_used(history) for entry in parsed.entries)

        # Test restaurants.md
        restaurants_file = examples_dir / 'restaurants.md'
        if restaurants_file.exists():
            parsed = parse_file(str(restaurants_file))
            assert len(parsed.entries) > 0
            assert 'Cuisine' in parsed.headers
            assert 'Price' in parsed.headers

        # Test exercises.md
        exercises_file = examples_dir / 'exercises.md'
        if exercises_file.exists():
            parsed = parse_file(str(exercises_file))
            assert len(parsed.entries) > 0
            assert 'Body Area' in parsed.headers
            assert 'Duration' in parsed.headers


def test_backwards_compatibility_with_used_column():
    """Test that files with the old 'Used' column are still parsed correctly."""
    content = """| Entry | Category | Used |
|-------|----------|------|
| First | Personal | [ ] |
| Second | Work | [x] |
| Third | Personal | [ ] |

<!-- QUIVER_METADATA
history: []
-->
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        parsed = parse_file(temp_path)

        # Should parse successfully
        assert len(parsed.entries) == 3

        # Headers should include Used (we keep it on parse)
        assert 'Used' in parsed.headers

        # Metadata should only include Category (not Used)
        assert parsed.entries[0].metadata == {'Category': 'Personal'}
        assert parsed.entries[1].metadata == {'Category': 'Work'}

        # All entries should be unused since history is empty
        # (the old Used column is ignored)
        history = parsed.metadata.get('history', [])
        assert all(not entry.is_used(history) for entry in parsed.entries)

        # When we serialize, Used column should be removed
        serialized = MarkdownTableParser.serialize_file(parsed)
        # Count occurrences of "Used" - should only appear once in old content
        # but not in the headers or data rows we generate
        lines = serialized.split('\n')
        header_line = [l for l in lines if l.startswith('| Entry')]
        assert len(header_line) == 1
        assert 'Used' not in header_line[0]

    finally:
        Path(temp_path).unlink()


if __name__ == '__main__':
    # Run tests manually
    test_parse_simple_table()
    test_parse_table_with_multiple_metadata_columns()
    test_parse_table_with_metadata()
    test_serialize_file()
    test_round_trip()
    test_parse_empty_metadata()
    test_parse_no_metadata()
    test_parse_file_not_found()
    test_parse_real_examples()
    test_backwards_compatibility_with_used_column()

    print("All parser tests passed!")
