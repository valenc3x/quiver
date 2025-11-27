"""Parser module for reading and writing markdown table files."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class Entry:
    """Represents a single entry from the markdown table."""
    content: str
    metadata: dict[str, str]
    row_index: int

    def is_used(self, history: List[int]) -> bool:
        """Check if this entry is marked as used in history."""
        return self.row_index in history


@dataclass
class ParsedFile:
    """Represents a parsed markdown file with entries and metadata."""
    entries: List[Entry]
    headers: List[str]
    metadata: dict = field(default_factory=dict)
    raw_content: str = ""
    filepath: str = ""


class MarkdownTableParser:
    """Parser for markdown tables with state tracking."""

    # Regex patterns
    TABLE_ROW_PATTERN = re.compile(r'^\|(.+)\|$')
    TABLE_SEPARATOR_PATTERN = re.compile(r'^\|[\s\-:|]+\|$')
    METADATA_PATTERN = re.compile(
        r'<!--\s*QUIVER_METADATA\s*\n(.*?)\n-->',
        re.DOTALL
    )

    @staticmethod
    def parse_file(filepath: str) -> ParsedFile:
        """
        Parse a markdown file containing a table.

        Args:
            filepath: Path to the markdown file

        Returns:
            ParsedFile object with entries and metadata

        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        content = path.read_text(encoding='utf-8')

        # Extract table and metadata
        table_data = MarkdownTableParser._extract_table(content)
        quiver_metadata = MarkdownTableParser._extract_metadata(content)

        # Parse entries from table
        entries = MarkdownTableParser._extract_entries_from_table(
            table_data['headers'],
            table_data['rows']
        )

        return ParsedFile(
            entries=entries,
            headers=table_data['headers'],
            metadata=quiver_metadata,
            raw_content=content,
            filepath=str(path.absolute())
        )

    @staticmethod
    def _extract_table(content: str) -> dict:
        """
        Extract table headers and rows from markdown content.

        Args:
            content: Raw markdown content

        Returns:
            Dictionary with 'headers' and 'rows' keys
        """
        lines = content.split('\n')
        headers = []
        rows = []
        in_table = False
        row_index = 0

        for line in lines:
            line = line.strip()

            # Check if this is a table row
            if MarkdownTableParser.TABLE_ROW_PATTERN.match(line):
                cells = [cell.strip() for cell in line.strip('|').split('|')]

                if not in_table:
                    # This is the header row
                    headers = cells
                    in_table = True
                elif MarkdownTableParser.TABLE_SEPARATOR_PATTERN.match(line):
                    # This is the separator row, skip it
                    continue
                else:
                    # This is a data row
                    rows.append({
                        'cells': cells,
                        'row_index': row_index
                    })
                    row_index += 1
            elif in_table and line and not line.startswith('#'):
                # Check for separator line (---|---|---)
                if MarkdownTableParser.TABLE_SEPARATOR_PATTERN.match(line):
                    continue
                # If we were in a table and hit a non-table line, we're done
                elif not MarkdownTableParser.TABLE_ROW_PATTERN.match(line):
                    break

        return {
            'headers': headers,
            'rows': rows
        }

    @staticmethod
    def _extract_entries_from_table(headers: List[str], rows: List[dict]) -> List[Entry]:
        """
        Convert table rows into Entry objects.

        Args:
            headers: List of column headers
            rows: List of row dictionaries with cells and row_index

        Returns:
            List of Entry objects
        """
        if not headers or len(headers) < 1:
            return []

        # Check if last column is "Used" (for backwards compatibility, we'll ignore it)
        has_used_column = headers[-1].lower() == 'used'

        entries = []

        for row_data in rows:
            cells = row_data['cells']
            row_index = row_data['row_index']

            # Skip rows that don't have enough cells
            if len(cells) < 1:
                continue

            # First column is the entry content
            content = cells[0]

            # Determine metadata column range
            # If there's a "Used" column, skip it; otherwise use all remaining columns
            metadata_end = len(cells) - 1 if has_used_column else len(cells)

            # Middle columns are metadata
            metadata = {}
            for i in range(1, metadata_end):
                if i < len(headers):
                    header = headers[i]
                    value = cells[i]
                    metadata[header] = value

            entries.append(Entry(
                content=content,
                metadata=metadata,
                row_index=row_index
            ))

        return entries

    @staticmethod
    def _extract_metadata(content: str) -> dict:
        """
        Extract QUIVER_METADATA from HTML comment in the file.

        Args:
            content: Raw markdown content

        Returns:
            Dictionary with metadata (history as list of indices, etc.)
        """
        match = MarkdownTableParser.METADATA_PATTERN.search(content)
        if not match:
            return {'history': []}

        metadata_str = match.group(1).strip()

        # Parse simple key: value format
        metadata = {'history': []}

        for line in metadata_str.split('\n'):
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()

                # Parse history as a list of integers
                if key == 'history':
                    # Remove brackets, split by comma
                    value = value.strip('[]')
                    if value:
                        # Split by comma and convert to integers
                        try:
                            items = [
                                int(item.strip().strip('"').strip("'"))
                                for item in value.split(',')
                                if item.strip()
                            ]
                            metadata['history'] = items
                        except ValueError:
                            # If parsing fails (e.g., old string format), reset to empty
                            # This provides backwards compatibility
                            metadata['history'] = []
                    else:
                        metadata['history'] = []
                else:
                    metadata[key] = value

        return metadata

    @staticmethod
    def serialize_file(parsed_file: ParsedFile) -> str:
        """
        Convert a ParsedFile back to markdown format.

        Args:
            parsed_file: ParsedFile object to serialize

        Returns:
            Markdown-formatted string
        """
        lines = []

        # Extract any content before the table (headers, etc.)
        original_lines = parsed_file.raw_content.split('\n')
        pre_table_lines = []
        in_table = False

        for line in original_lines:
            if MarkdownTableParser.TABLE_ROW_PATTERN.match(line.strip()):
                in_table = True
                break
            elif not line.strip().startswith('<!--'):
                pre_table_lines.append(line)

        # Add pre-table content
        if pre_table_lines:
            lines.extend(pre_table_lines)
            if not lines[-1].strip():
                pass  # Already has blank line
            else:
                lines.append('')

        # Filter out "Used" column from headers if present
        headers = [h for h in parsed_file.headers if h.lower() != 'used']

        # Build table header
        header_row = '| ' + ' | '.join(headers) + ' |'
        lines.append(header_row)

        # Build separator row
        separator = '|' + '|'.join(['---' for _ in headers]) + '|'
        lines.append(separator)

        # Build data rows
        for entry in parsed_file.entries:
            cells = [entry.content]

            # Add metadata columns in header order (excluding "Used")
            for header in headers[1:]:  # Skip first (Entry)
                cells.append(entry.metadata.get(header, ''))

            row = '| ' + ' | '.join(cells) + ' |'
            lines.append(row)

        # Add metadata comment at the end
        if parsed_file.metadata:
            lines.append('')
            lines.append('<!-- QUIVER_METADATA')

            # Serialize history as integers
            if 'history' in parsed_file.metadata:
                history = parsed_file.metadata['history']
                if history:
                    history_str = ', '.join([str(idx) for idx in history])
                    lines.append(f'history: [{history_str}]')
                else:
                    lines.append('history: []')

            lines.append('-->')

        return '\n'.join(lines)

    @staticmethod
    def save_file(parsed_file: ParsedFile) -> None:
        """
        Save a ParsedFile back to disk.

        Args:
            parsed_file: ParsedFile object to save
        """
        content = MarkdownTableParser.serialize_file(parsed_file)
        path = Path(parsed_file.filepath)
        path.write_text(content, encoding='utf-8')


# Convenience functions for external use
def parse_file(filepath: str) -> ParsedFile:
    """Parse a markdown file."""
    return MarkdownTableParser.parse_file(filepath)


def save_file(parsed_file: ParsedFile) -> None:
    """Save a parsed file back to disk."""
    return MarkdownTableParser.save_file(parsed_file)
