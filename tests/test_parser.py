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

| Entry | Category | Used |
|-------|----------|------|
| First entry | Personal | [ ] |
| Second entry | Work | [x] |
| Third entry | Personal | [ ] |
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        parsed = parse_file(temp_path)

        # Check headers
        assert parsed.headers == ['Entry', 'Category', 'Used']

        # Check entries
        assert len(parsed.entries) == 3

        # First entry
        assert parsed.entries[0].content == 'First entry'
        assert parsed.entries[0].metadata == {'Category': 'Personal'}
        assert parsed.entries[0].used is False

        # Second entry
        assert parsed.entries[1].content == 'Second entry'
        assert parsed.entries[1].metadata == {'Category': 'Work'}
        assert parsed.entries[1].used is True

        # Third entry
        assert parsed.entries[2].content == 'Third entry'
        assert parsed.entries[2].metadata == {'Category': 'Personal'}
        assert parsed.entries[2].used is False

    finally:
        Path(temp_path).unlink()


def test_parse_table_with_multiple_metadata_columns():
    """Test parsing a table with multiple metadata columns."""
    content = """| Restaurant | Cuisine | Price | Used |
|------------|---------|-------|------|
| Mario's Pizza | Italian | $$ | [ ] |
| Sushi House | Japanese | $$$ | [x] |
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        parsed = parse_file(temp_path)

        assert len(parsed.entries) == 2

        # First entry
        assert parsed.entries[0].content == "Mario's Pizza"
        assert parsed.entries[0].metadata == {
            'Cuisine': 'Italian',
            'Price': '$$'
        }
        assert parsed.entries[0].used is False

        # Second entry
        assert parsed.entries[1].content == 'Sushi House'
        assert parsed.entries[1].metadata == {
            'Cuisine': 'Japanese',
            'Price': '$$$'
        }
        assert parsed.entries[1].used is True

    finally:
        Path(temp_path).unlink()


def test_parse_table_with_metadata():
    """Test parsing a table with QUIVER_METADATA."""
    content = """| Entry | Category | Used |
|-------|----------|------|
| First entry | Personal | [x] |
| Second entry | Work | [ ] |

<!-- QUIVER_METADATA
history: ["First entry"]
-->
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        parsed = parse_file(temp_path)

        assert len(parsed.entries) == 2
        assert parsed.metadata['history'] == ['First entry']

    finally:
        Path(temp_path).unlink()


def test_serialize_file():
    """Test serializing a ParsedFile back to markdown."""
    # Create a parsed file
    entries = [
        Entry(
            content='First entry',
            metadata={'Category': 'Personal'},
            used=False,
            row_index=0
        ),
        Entry(
            content='Second entry',
            metadata={'Category': 'Work'},
            used=True,
            row_index=1
        )
    ]

    parsed = ParsedFile(
        entries=entries,
        headers=['Entry', 'Category', 'Used'],
        metadata={'history': ['Second entry']},
        raw_content='',
        filepath=''
    )

    # Serialize
    result = MarkdownTableParser.serialize_file(parsed)

    # Check that it contains expected parts
    assert '| Entry | Category | Used |' in result
    assert '| First entry | Personal | [ ] |' in result
    assert '| Second entry | Work | [x] |' in result
    assert '<!-- QUIVER_METADATA' in result
    assert 'history: ["Second entry"]' in result


def test_round_trip():
    """Test parsing and serializing maintains data integrity."""
    original_content = """# My List

| Entry | Category | Used |
|-------|----------|------|
| First entry | Personal | [ ] |
| Second entry | Work | [x] |

<!-- QUIVER_METADATA
history: ["Second entry"]
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
        assert parsed.entries[0].used is False
        assert parsed.entries[1].content == 'Second entry'
        assert parsed.entries[1].used is True
        assert parsed.metadata['history'] == ['Second entry']

        # Modify an entry
        parsed.entries[0].used = True
        parsed.metadata['history'].insert(0, 'First entry')

        # Save back
        save_file(parsed)

        # Re-parse
        parsed2 = parse_file(temp_path)

        # Verify changes persisted
        assert parsed2.entries[0].used is True
        assert parsed2.entries[1].used is True
        assert parsed2.metadata['history'] == ['First entry', 'Second entry']

    finally:
        Path(temp_path).unlink()


def test_parse_empty_metadata():
    """Test parsing a file with empty QUIVER_METADATA."""
    content = """| Entry | Used |
|-------|------|
| Test | [ ] |

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
    content = """| Entry | Used |
|-------|------|
| Test | [ ] |
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
    import os

    # Get the examples directory
    examples_dir = Path(__file__).parent.parent / 'examples'

    if examples_dir.exists():
        # Test prompts.md
        prompts_file = examples_dir / 'prompts.md'
        if prompts_file.exists():
            parsed = parse_file(str(prompts_file))
            assert len(parsed.entries) > 0
            assert 'Category' in parsed.headers
            assert all(not entry.used for entry in parsed.entries)

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


def test_case_insensitive_used_status():
    """Test that [X] and [x] are both recognized as used."""
    content = """| Entry | Used |
|-------|------|
| First | [x] |
| Second | [X] |
| Third | [ ] |
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        parsed = parse_file(temp_path)

        assert parsed.entries[0].used is True  # [x]
        assert parsed.entries[1].used is True  # [X]
        assert parsed.entries[2].used is False  # [ ]

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
    test_case_insensitive_used_status()

    print("All tests passed!")
