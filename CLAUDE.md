# Quiver

## Project Overview

A lightweight Python CLI tool named **quiver** for randomly selecting entries from markdown tables, with state tracking, metadata support, and rollback capabilities.

## Problem Statement

Managing daily habits like journaling prompts, restaurant choices, or read-later lists often requires:
- **Random selection** to avoid decision fatigue
- **State tracking** to prevent repeating recent items
- **Flexibility** to undo selections when plans change
- **Simple reset** to start fresh without manual editing

## Core Requirements

### Functional Requirements
1. **Random Selection**: Pick a random unused entry from a markdown table
2. **Metadata Support**: Additional table columns are returned as metadata (e.g., cuisine type, genre, body area)
3. **State Management**: Mark entries as "used" after selection
4. **Exclusion Logic**: Never return already-used entries
5. **Reverse Rollback**: Undo last selection(s) in LIFO order
6. **Full Reset**: Mark all entries as unused
7. **Format**: Well-formatted markdown table input/output

### Non-Functional Requirements
- Simple CLI interface
- Minimal dependencies (ideally just Python stdlib)
- Clear, readable markdown format
- Preserve formatting when modifying files
- Human-readable state tracking

## Use Cases

1. **Daily journaling prompts**: Pick today's prompt (with category metadata like "Personal", "Gratitude")
2. **Restaurant picker**: Choose dinner spot with cuisine type (Italian, Japanese, Mexican)
3. **Reading list**: Select next article with topic/author metadata
4. **Exercise routines**: Random workout with body area (Upper, Lower, Core, Cardio)
5. **Movie/book lists**: Random selection with genre metadata (Sci-Fi, Drama, Comedy)
6. **Any list-based random selection** with flexible metadata columns

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
