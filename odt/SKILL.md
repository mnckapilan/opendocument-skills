---
name: odt
description: >
  Work with ODT (OpenDocument Text) files — the document format used by
  LibreOffice, OpenOffice, and other open-source office suites. Use when the
  user wants to read, write, create, or modify .odt files: reading paragraphs
  and headings, appending or inserting content, replacing text, or querying
  document structure.
license: MIT
compatibility: Requires uv and Python 3.11+
allowed-tools: Bash(uv:*)
---

# ODT skill

Read and write ODT text document files using `scripts/odt.py`.

**Prerequisite:** [`uv`](https://docs.astral.sh/uv/) must be installed.
Install it with: `curl -LsSf https://astral.sh/uv/install.sh | sh`

## Available scripts

- **`scripts/odt.py`** — All ODT operations via subcommands (see below).

Run `uv run scripts/odt.py --help` for the full command list, or
`uv run scripts/odt.py <command> --help` for per-command usage.

## Commands

| Command | What it does |
|---|---|
| `file-info <file>` | Title, paragraph/heading counts, word count — start here when exploring |
| `read-text <file>` | All blocks as JSON; supports `--offset N` and `--limit N` |
| `get-paragraph <file> --index N` | Single block by 0-based index |
| `set-paragraph <file> --index N --text T [--style S]` | Replace a block's text |
| `append-paragraph <file> --text T [--style S]` | Append a block at the end |
| `insert-paragraph <file> --index N --text T [--style S]` | Insert before index N |
| `delete-paragraph <file> --index N --confirm` | Delete a block |
| `list-headings <file>` | Heading blocks with level and index |
| `find-replace <file> --find T --replace T [--dry-run]` | Find and replace text |
| `create <file> [--title T] [--overwrite]` | Create a new ODT file |

**Styles** for `--style`: `default`, `h1`–`h6` (headings), `title`, `subtitle`.
Any other value is used as a named paragraph style as-is.

## Block indexing

Paragraphs and headings are numbered sequentially from 0. `read-text` and
`list-headings` both show each block's index. Use `file-info` first to see
total counts, then `read-text` to browse content before editing.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Invalid arguments |
| 2 | File not found |
| 3 | Block index out of range |
| 5 | ODF parse or write error |

## Gotchas

- **Always use `uv run`** — invoke as `uv run scripts/odt.py <command>`, never `python scripts/odt.py`. Dependencies are declared as PEP 723 inline metadata and installed by uv.
- **`set-paragraph` and `find-replace` lose inline formatting** — they rebuild the block element, so bold, italic, and other character-level formatting within modified blocks is not preserved.
- **Only direct paragraphs and headings are indexed** — blocks nested inside tables, text frames, or other containers are not included in the block list. For typical prose documents this is rarely an issue.
- **`create` fails if the file exists** — pass `--overwrite` only after confirming with the user.
- **`delete-paragraph --confirm` is irreversible** — always verify with the user before passing this flag.

## Workflow guidance

**Exploring a document** — run `file-info` first for counts, then `read-text`
to browse content. For long documents use `--limit` and `--offset` to page
through blocks rather than reading everything at once.

**Editing content** — `append-paragraph` for adding to the end; `insert-paragraph`
for inserting at a specific position; `set-paragraph` for replacing text in place.
`find-replace --dry-run` previews changes before committing.

**Destructive operations** — confirm with the user before passing `--confirm`
to `delete-paragraph` or `--overwrite` to `create`.

## Examples

```bash
# Explore a document
uv run scripts/odt.py file-info report.odt

# Read the first 10 blocks
uv run scripts/odt.py read-text report.odt --limit 10

# Read blocks 10–19 (second page)
uv run scripts/odt.py read-text report.odt --offset 10 --limit 10

# Get a specific block
uv run scripts/odt.py get-paragraph report.odt --index 3

# List all headings (with their indices)
uv run scripts/odt.py list-headings report.odt

# Append a plain paragraph
uv run scripts/odt.py append-paragraph report.odt --text "See appendix for details."

# Append a heading
uv run scripts/odt.py append-paragraph report.odt --text "Conclusion" --style h1

# Insert a paragraph before block 2
uv run scripts/odt.py insert-paragraph report.odt --index 2 --text "Additional context."

# Replace the text at index 5
uv run scripts/odt.py set-paragraph report.odt --index 5 --text "Updated text."

# Preview a find-replace without saving
uv run scripts/odt.py find-replace report.odt --find "draft" --replace "final" --dry-run

# Apply the find-replace
uv run scripts/odt.py find-replace report.odt --find "draft" --replace "final"

# Delete a block (ask user before passing --confirm)
uv run scripts/odt.py delete-paragraph report.odt --index 7 --confirm

# Create a new document with a title
uv run scripts/odt.py create memo.odt --title "Weekly Memo"
```
