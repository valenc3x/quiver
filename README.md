# Quiver 🎯

A lightweight Python CLI tool for randomly selecting entries from markdown tables, with state tracking, metadata support, and rollback capabilities.

## Features

- 🎲 **Random Selection**: Pick a random unused entry from a markdown table
- 📊 **Metadata Support**: Additional table columns returned as metadata (cuisine, genre, body area, etc.)
- 💾 **State Persistence**: Automatically tracks which entries have been used
- ↩️ **LIFO Rollback**: Undo selections in reverse order
- 🔄 **Full Reset**: Mark all entries as unused with one command
- 📝 **Human-Readable Format**: Standard markdown tables you can edit
- 🚀 **Zero Dependencies**: Uses only Python standard library

## Installation

```bash
# Install from source
git clone https://github.com/valenc3x/quiver.git
cd quiver
pip install -e .
```

After installation, the `quiver` command will be available in your terminal.

## Quick Start

### 1. Create a markdown table

Create a file called `prompts.md`:

```markdown
# Daily Journaling Prompts

| Entry | Category |
|-------|----------|
| Write about a childhood memory | Personal |
| Describe your ideal day | Future |
| What are you grateful for today? | Gratitude |
| Reflect on a recent challenge | Growth |
```

**Format Rules:**
- First column: Entry content (required)
- Additional columns: Any metadata you want (optional)

### 2. Pick a random entry

```bash
$ quiver pick prompts.md
🎯 What are you grateful for today?
   Category: Gratitude
```

The entry is automatically marked as used!

### 3. Check status

```bash
$ quiver status prompts.md
📊 Status: 1/4 entries used (3 remaining)
```

### 4. Changed your mind? Rollback!

```bash
$ quiver rollback prompts.md
↩️  Rolled back: "What are you grateful for today?"
```

### 5. Start over

```bash
$ quiver reset prompts.md
🔄 Reset complete: 4 entries marked as unused
```

## Use Cases

### Restaurant Picker

```markdown
| Restaurant | Cuisine | Price |
|------------|---------|-------|
| Mario's Pizza | Italian | $$ |
| Sushi House | Japanese | $$$ |
| Taco Loco | Mexican | $ |
```

```bash
$ quiver pick restaurants.md
🎯 Mario's Pizza
   Cuisine: Italian
   Price: $$
```

### Exercise Routines

```markdown
| Exercise | Body Area | Duration |
|----------|-----------|----------|
| Push-ups | Upper | 10 min |
| Squats | Lower | 15 min |
| Planks | Core | 5 min |
```

```bash
$ quiver pick exercises.md
🎯 Push-ups
   Body Area: Upper
   Duration: 10 min
```

### Reading List

```markdown
| Article | Topic | Author |
|---------|-------|--------|
| Clean Code Principles | Programming | Robert Martin |
| The Art of Debugging | Programming | Norman Matloff |
| Atomic Habits | Self-Help | James Clear |
```

## Commands

### `pick` - Select a random entry

```bash
quiver pick <file>
```

Picks a random unused entry and marks it as used. Displays the entry with all metadata.

**Options:**
- `--dry-run`: Preview without making changes
- `--verbose`: Show remaining entries count

**Examples:**
```bash
$ quiver pick prompts.md
$ quiver pick --dry-run restaurants.md
$ quiver pick --verbose exercises.md
```

### `rollback` - Undo last selection

```bash
quiver rollback <file>
```

Undoes the most recent selection in LIFO (Last-In-First-Out) order.

**Examples:**
```bash
$ quiver rollback prompts.md
↩️  Rolled back: "What are you grateful for today?"
```

### `reset` - Mark all entries as unused

```bash
quiver reset <file>
```

Marks all entries as unused and clears the history.

**Examples:**
```bash
$ quiver reset prompts.md
🔄 Reset complete: 4 entries marked as unused
```

### `status` - Show statistics

```bash
quiver status <file>
```

Shows usage statistics for the file.

**Options:**
- `--verbose`: Show history and metadata columns

**Examples:**
```bash
$ quiver status prompts.md
📊 Status: 2/8 entries used (6 remaining)

$ quiver status --verbose prompts.md
📊 Status: 2/8 entries used (6 remaining)

   History (2 items):
     1. Second entry
     2. First entry

   Metadata columns: Category
```

## Global Options

### `--dry-run`

Preview the action without modifying the file:

```bash
$ quiver --dry-run pick prompts.md
🎯 What are you grateful for today?
   Category: Gratitude

   (Dry run - no changes made)
```

### `--verbose`

Show detailed output:

```bash
$ quiver --verbose pick prompts.md
🎯 What are you grateful for today?
   Category: Gratitude

   Remaining: 7/8
```

### `--version`

Show version information:

```bash
$ quiver --version
quiver 0.1.0
```

## File Format Details

### Basic Structure

```markdown
| Entry | [Metadata Columns...] |
|-------|----------------------|
| ...   | ...                  |
```

### State Tracking

Quiver automatically adds a metadata comment at the end of the file to track selection history using row indices:

```markdown
<!-- QUIVER_METADATA
history: [0, 3, 1]
-->
```

This tracks which entries have been selected by their row position (0-indexed). This enables LIFO rollback functionality.

**How it works:**
- When you pick an entry, its row index is added to the history
- Used entries are those whose indices appear in the history
- Rollback removes the last index from history (LIFO order)

### Important Limitations

⚠️ **Manual Editing Warnings:**

1. **Adding entries**: Safe to add new entries at the end of the table
2. **Editing content**: Safe to edit entry text or metadata in existing rows
3. **Removing entries**: If you delete rows, run `quiver reset` to clear the history, as indices will become invalid
4. **Reordering rows**: DO NOT reorder rows if there's existing history - this will corrupt the tracking. If you need to reorder, run `quiver reset` first

**What happens if you violate these rules:**
- If the table becomes smaller and history contains out-of-bounds indices, you'll get an error message: "History contains invalid index X. Run 'quiver reset' to clear history."
- If you reorder rows with existing history, previously-used entries may appear as unused and vice versa

**Safe workflow for major edits:**
1. Run `quiver reset <file>` to clear history
2. Make your edits (reorder, delete, add rows)
3. Start using `quiver pick` again

### Tips

1. **Any number of metadata columns**: Add as many metadata columns as you need
2. **Edit content safely**: You can modify entry text and metadata values without issues
3. **Multiple tables**: Create different files for different purposes (prompts, restaurants, exercises, etc.)
4. **Version control friendly**: The format is plain text, perfect for git
5. **Backwards compatible**: Old files with a "Used" column will still work (the column is ignored)

## Development

### Running Tests

```bash
# Run all tests
python -m tests.test_parser
python -m tests.test_selector
python -m tests.test_state
python -m tests.test_rollback
python -m tests.test_cli
```

### Project Structure

```
quiver/
├── quiver/
│   ├── __init__.py       # Package info
│   ├── cli.py            # CLI interface
│   ├── parser.py         # Markdown table parsing
│   ├── selector.py       # Random selection logic
│   ├── state.py          # State management
│   └── rollback.py       # Rollback functionality
├── tests/
│   ├── test_parser.py    # Parser tests
│   ├── test_selector.py  # Selector tests
│   ├── test_state.py     # State tests
│   ├── test_rollback.py  # Rollback tests
│   └── test_cli.py       # CLI integration tests
├── examples/
│   ├── prompts.md        # Example: journaling prompts
│   ├── restaurants.md    # Example: restaurant picker
│   └── exercises.md      # Example: exercise routines
├── setup.py              # Package setup
├── CLAUDE.md             # Project overview
├── PROJECT_PLAN.md       # Implementation plan
└── README.md             # This file
```

## Requirements

- Python 3.8 or higher
- No external dependencies!

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - See LICENSE file for details

## Acknowledgments

Built with ❤️ as a practical solution for decision fatigue and habit tracking.

---

**Happy picking! 🎯**
