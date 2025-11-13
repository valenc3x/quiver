# Random Prompt Picker

## Project Overview

A lightweight Python CLI tool for randomly selecting entries from a markdown-formatted list, with state tracking and rollback capabilities.

## Problem Statement

Managing daily habits like journaling prompts, restaurant choices, or read-later lists often requires:
- **Random selection** to avoid decision fatigue
- **State tracking** to prevent repeating recent items
- **Flexibility** to undo selections when plans change
- **Simple reset** to start fresh without manual editing

## Core Requirements

### Functional Requirements
1. **Random Selection**: Pick a random unused entry from a markdown file
2. **State Management**: Mark entries as "used" after selection
3. **Exclusion Logic**: Never return already-used entries
4. **Reverse Rollback**: Undo last selection(s) in LIFO order
5. **Full Reset**: Mark all entries as unused
6. **Format**: Well-formatted markdown input/output

### Non-Functional Requirements
- Simple CLI interface
- Minimal dependencies (ideally just Python stdlib)
- Clear, readable markdown format
- Preserve formatting when modifying files
- Human-readable state tracking

## Use Cases

1. **Daily journaling prompts**: Pick today's prompt, mark as used
2. **Restaurant picker**: Choose dinner spot, rollback if plans change
3. **Reading list**: Select next article, track progress
4. **Exercise routines**: Random workout selection
5. **Any list-based random selection** with progress tracking

## Success Criteria

- ✅ Can parse markdown file with entries
- ✅ Randomly selects unused entries
- ✅ Persists state between runs
- ✅ Supports single-entry rollback (LIFO)
- ✅ Supports full reset
- ✅ Maintains markdown readability
- ✅ Clear error messages for edge cases

## Out of Scope (v1)

- Web interface
- Multiple file management
- Weighted/priority selection
- Scheduling/reminders
- Analytics/statistics

## Next Steps

See PROJECT_PLAN.md for detailed implementation plan.
