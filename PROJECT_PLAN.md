# Project Plan: Random Prompt Picker

## 1. File Format Specification

### Markdown Entry Format

Each entry should be a markdown list item with a status indicator:

```markdown
# My Prompts

- [ ] Write about a childhood memory
- [ ] Describe your ideal day
- [x] What are you grateful for today?
- [ ] Reflect on a recent challenge

## Section 2

- [ ] Another prompt here
```

**Format Rules:**
- `- [ ]` = Unused/available entry
- `- [x]` = Used entry
- Supports markdown headers for organization
- Entry content = everything after the checkbox
- Blank lines and comments preserved

**Metadata Storage (bottom of file):**
```markdown
<!-- PICKER_METADATA
history: ["What are you grateful for today?"]
-->
```

This tracks selection order for LIFO rollback.

## 2. Architecture Design

### Components

```
random_prompt_picker/
├── picker.py           # Main CLI interface
├── parser.py           # Markdown parsing logic
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
└── sample_prompts.md

README.md
requirements.txt
```

### Data Flow

```
User Command
    ↓
CLI (picker.py)
    ↓
Parser (parser.py) → Parse markdown → Entry objects
    ↓
Selector (selector.py) → Filter unused → Random choice
    ↓
State Manager (state.py) → Mark as used → Update file
    ↓
Display result to user
```

## 3. Module Specifications

### parser.py

**Responsibilities:**
- Read markdown file
- Parse checkbox list items
- Extract metadata (history)
- Preserve formatting (headers, blank lines)

**Key Functions:**
```python
def parse_file(filepath: str) -> ParsedFile
def extract_entries(content: str) -> List[Entry]
def extract_metadata(content: str) -> dict
def serialize_file(parsed_file: ParsedFile) -> str
```

**Data Structures:**
```python
@dataclass
class Entry:
    content: str
    used: bool
    line_number: int
    original_line: str

@dataclass
class ParsedFile:
    entries: List[Entry]
    metadata: dict
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

### picker.py (CLI)

**Responsibilities:**
- Command-line argument parsing
- User interaction
- Command routing

**Commands:**
```bash
python picker.py pick <file>           # Get random entry
python picker.py rollback <file>       # Undo last pick
python picker.py reset <file>          # Reset all entries
python picker.py status <file>         # Show stats (used/total)
```

**CLI Design with argparse:**
```python
# Main commands
pick      - Select random unused entry
rollback  - Undo last selection
reset     - Mark all entries as unused
status    - Show usage statistics

# Optional flags
--file, -f    - Path to markdown file (can set default)
--dry-run     - Preview without modifying file
--verbose, -v - Show detailed output
```

## 4. Implementation Phases

### Phase 1: Core Parsing (Foundation)
- [x] Create project structure
- [ ] Implement parser.py
  - Parse markdown checkboxes
  - Extract entries
  - Handle metadata section
- [ ] Write tests for parser
- [ ] Create sample markdown files

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
- [ ] Implement picker.py
  - Argument parsing
  - Command routing
  - User-friendly output
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

4. **Malformed markdown**: Invalid checkbox syntax
   - Warning: Skip invalid lines, continue with valid entries

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

```bash
# Pick a random unused entry
$ python picker.py pick prompts.md
✨ Your prompt: "Write about a childhood memory"

# Oops, not today - rollback
$ python picker.py rollback prompts.md
↩️  Rolled back: "Write about a childhood memory"

# Pick another one
$ python picker.py pick prompts.md
✨ Your prompt: "Describe your ideal day"

# Check status
$ python picker.py status prompts.md
📊 Status: 2/10 entries used (8 remaining)

# Start over
$ python picker.py reset prompts.md
🔄 Reset complete: 10 entries marked as unused
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

- **Multiple files**: Manage different lists
- **Weighted selection**: Priority/weight per entry
- **Tags/categories**: Filter by category
- **Statistics**: Most/least picked, streaks
- **Config file**: Set default file path, preferences
- **Interactive mode**: TUI with arrow key selection
- **Export**: Generate reports of used/unused entries
- **Scheduling**: Integrate with cron for daily picks

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
