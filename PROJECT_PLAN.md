# Project Plan: Quiver

## 1. File Format Specification

### Markdown Table Format

Entries are stored in markdown tables with flexible columns:

**Basic Format (Prompts):**
```markdown
| Entry | Category | Used |
|-------|----------|------|
| Write about a childhood memory | Personal | [ ] |
| Describe your ideal day | Future | [ ] |
| What are you grateful for today? | Gratitude | [x] |
| Reflect on a recent challenge | Growth | [ ] |
```

**Restaurant Format:**
```markdown
| Restaurant | Cuisine | Price | Used |
|------------|---------|-------|------|
| Mario's Pizza | Italian | $$ | [ ] |
| Sushi House | Japanese | $$$ | [x] |
| Taco Loco | Mexican | $ | [ ] |
```

**Exercise Format:**
```markdown
| Exercise | Body Area | Duration | Used |
|----------|-----------|----------|------|
| Push-ups | Upper | 10 min | [ ] |
| Squats | Lower | 15 min | [x] |
| Planks | Core | 5 min | [ ] |
```

**Format Rules:**
- First column: Entry content (required)
- Last column: `Used` status with `[ ]` or `[x]` (required)
- Middle columns: Flexible metadata (optional, any number)
- Headers must be present
- Pipe-delimited markdown table format

**Metadata Storage (bottom of file):**
```markdown
<!-- QUIVER_METADATA
history: ["What are you grateful for today?"]
-->
```

This tracks selection order for LIFO rollback.

## 2. Architecture Design

### Components

```
quiver/
├── cli.py              # Main CLI interface (entry point)
├── parser.py           # Markdown table parsing logic
├── selector.py         # Random selection logic
├── state.py            # State management (mark used/unused)
├── rollback.py         # Rollback logic
└── utils.py            # Helper functions

tests/
├── test_parser.py
├── test_selector.py
├── test_state.py
└── test_rollback.py

examples/
├── sample_prompts.md
├── restaurants.md
└── exercises.md

README.md
setup.py                # For pip install
```

### Data Flow

```
User Command
    ↓
CLI (cli.py)
    ↓
Parser (parser.py) → Parse markdown table → Entry objects with metadata
    ↓
Selector (selector.py) → Filter unused → Random choice
    ↓
State Manager (state.py) → Mark as used → Update file
    ↓
Display result with metadata to user
```

## 3. Module Specifications

### parser.py

**Responsibilities:**
- Read markdown file
- Parse markdown table rows
- Extract entry content, metadata columns, and used status
- Extract QUIVER_METADATA (history)
- Preserve table formatting

**Key Functions:**
```python
def parse_file(filepath: str) -> ParsedFile
def extract_table(content: str) -> Table
def extract_entries_from_table(table: Table) -> List[Entry]
def extract_metadata(content: str) -> dict
def serialize_file(parsed_file: ParsedFile) -> str
```

**Data Structures:**
```python
@dataclass
class Entry:
    content: str              # First column value
    metadata: dict[str, str]  # Middle columns as key-value pairs
    used: bool                # Last column status
    row_index: int            # Position in table

@dataclass
class ParsedFile:
    entries: List[Entry]
    headers: List[str]        # Table column headers
    metadata: dict            # QUIVER_METADATA (history, etc.)
    raw_content: str
    filepath: str
```

### selector.py

**Responsibilities:**
- Filter available entries
- Random selection
- Handle empty list case

**Key Functions:**
```python
def get_available_entries(entries: List[Entry]) -> List[Entry]
def select_random(entries: List[Entry]) -> Entry | None
```

### state.py

**Responsibilities:**
- Mark entry as used
- Update markdown file
- Maintain metadata
- Preserve formatting

**Key Functions:**
```python
def mark_entry_used(parsed_file: ParsedFile, entry: Entry) -> None
def mark_entry_unused(parsed_file: ParsedFile, entry: Entry) -> None
def save_file(parsed_file: ParsedFile) -> None
def add_to_history(parsed_file: ParsedFile, entry: Entry) -> None
def remove_from_history(parsed_file: ParsedFile) -> Entry | None
```

### rollback.py

**Responsibilities:**
- LIFO rollback (undo last pick)
- Full reset (mark all unused)

**Key Functions:**
```python
def rollback_last(filepath: str) -> Entry | None
def reset_all(filepath: str) -> int  # Returns count of reset entries
```

### cli.py (CLI Entry Point)

**Responsibilities:**
- Command-line argument parsing
- User interaction
- Command routing
- Display entry with metadata

**Commands:**
```bash
quiver pick <file>           # Get random entry with metadata
quiver rollback <file>       # Undo last pick
quiver reset <file>          # Reset all entries
quiver status <file>         # Show stats (used/total)
```

**CLI Design with argparse:**
```python
# Main commands
pick      - Select random unused entry, display with metadata
rollback  - Undo last selection
reset     - Mark all entries as unused
status    - Show usage statistics

# Optional flags
--file, -f    - Path to markdown file (can set default)
--dry-run     - Preview without modifying file
--verbose, -v - Show detailed output
```

**Output Example:**
```bash
$ quiver pick restaurants.md
🎯 Mario's Pizza
   Cuisine: Italian
   Price: $$
```

## 4. Implementation Phases

### Phase 1: Core Parsing (Foundation)
- [x] Create project structure
- [ ] Implement parser.py
  - Parse markdown tables
  - Extract entries with metadata columns
  - Handle QUIVER_METADATA section
- [ ] Write tests for parser
- [ ] Create sample markdown files (prompts, restaurants, exercises)

### Phase 2: Selection Logic
- [ ] Implement selector.py
  - Filter available entries
  - Random selection
- [ ] Implement state.py
  - Mark entries used/unused
  - Update file with preserved formatting
  - Maintain history metadata
- [ ] Write tests for selector and state

### Phase 3: Rollback Features
- [ ] Implement rollback.py
  - LIFO rollback using history
  - Full reset functionality
- [ ] Write tests for rollback

### Phase 4: CLI Interface
- [ ] Implement cli.py
  - Argument parsing with argparse
  - Command routing (pick, rollback, reset, status)
  - User-friendly output with metadata display
  - Setup.py for `quiver` command installation
- [ ] Add error handling
- [ ] Integration tests

### Phase 5: Polish
- [ ] Add status command (show stats)
- [ ] Add --dry-run flag
- [ ] Write README with examples
- [ ] Add example markdown files
- [ ] Manual testing with real-world use cases

## 5. Edge Cases & Error Handling

### Edge Cases to Handle

1. **Empty file**: No entries found
   - Error: "No entries found in file"

2. **All entries used**: No available entries
   - Error: "All entries have been used. Use 'reset' to start over."

3. **Rollback on empty history**: Nothing to rollback
   - Error: "No entries to rollback"

4. **Malformed markdown**: Invalid table syntax or missing columns
   - Warning: Skip invalid rows, continue with valid entries

5. **File doesn't exist**: Invalid path
   - Error: "File not found: <path>"

6. **Concurrent modification**: File changed externally
   - Use file locking or detect changes via checksum

7. **Very large files**: Performance considerations
   - Limit or warn if file > 10k entries

8. **Unicode/special characters**: Preserve encoding
   - Use UTF-8 encoding

### Error Handling Strategy

- **Graceful degradation**: Warn and continue when possible
- **Clear error messages**: Tell user what went wrong and how to fix
- **Validation**: Check file format before processing
- **Backup**: Consider backing up before modification (optional)

## 6. CLI Examples

**Journaling Prompts:**
```bash
$ quiver pick prompts.md
🎯 Write about a childhood memory
   Category: Personal

$ quiver rollback prompts.md
↩️  Rolled back: "Write about a childhood memory"
```

**Restaurant Picker:**
```bash
$ quiver pick restaurants.md
🎯 Mario's Pizza
   Cuisine: Italian
   Price: $$

$ quiver status restaurants.md
📊 Status: 3/15 restaurants used (12 remaining)
```

**Exercise Routine:**
```bash
$ quiver pick exercises.md
🎯 Push-ups
   Body Area: Upper
   Duration: 10 min

$ quiver reset exercises.md
🔄 Reset complete: 20 exercises marked as unused
```

## 7. Testing Strategy

### Unit Tests
- Parser: Correctly extracts entries, metadata
- Selector: Random selection, filtering
- State: Marks used/unused, preserves formatting
- Rollback: LIFO order, full reset

### Integration Tests
- End-to-end: pick → use file state → rollback
- File I/O: Read → modify → write → verify
- Multiple operations: pick → pick → rollback → pick

### Manual Testing
- Real-world markdown files
- Different entry formats
- Edge cases (empty, all used, etc.)

## 8. Future Enhancements (Post-v1)

- **Multiple files**: Manage different lists, switch between them
- **Weighted selection**: Priority/weight per entry
- **Filter by metadata**: `quiver pick --cuisine Italian restaurants.md`
- **Statistics**: Most/least picked, streaks, usage patterns
- **Config file**: Set default file path, preferences
- **Interactive mode**: TUI with arrow key selection
- **Export**: Generate reports of used/unused entries
- **Scheduling**: Integrate with cron for daily picks
- **Validation**: Validate table format, suggest fixes

## 9. Dependencies

**Required:**
- Python 3.8+ (for dataclasses, type hints)
- Standard library only (argparse, random, re, dataclasses)

**Optional (for development):**
- pytest (testing)
- black (formatting)
- mypy (type checking)
- coverage (test coverage)

## 10. Timeline Estimate

- **Phase 1** (Parsing): 2-3 hours
- **Phase 2** (Selection/State): 2-3 hours
- **Phase 3** (Rollback): 1-2 hours
- **Phase 4** (CLI): 1-2 hours
- **Phase 5** (Polish): 1-2 hours

**Total**: ~7-12 hours for complete implementation

## Next Steps

1. Review this plan with stakeholder (you!)
2. Create sample markdown file for testing
3. Begin Phase 1: Implement parser.py
4. Iterate with feedback

---

**Ready to start coding?** Let me know if you want to adjust the plan or if we should proceed with implementation!
