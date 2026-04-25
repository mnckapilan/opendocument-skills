---
name: ods
description: >
  Work with ODS (OpenDocument Spreadsheet) files — the spreadsheet format used
  by LibreOffice, OpenOffice, and other open-source office suites. Use when the
  user wants to read, write, create, or modify .ods files: listing sheets,
  reading tabular data, getting or setting cells, appending rows, or managing
  sheets.
license: MIT
compatibility: Requires uv and Python 3.11+
allowed-tools: Bash(uv:*)
---

# ODS skill

Read and write ODS spreadsheet files using `scripts/ods.py`.

**Prerequisite:** [`uv`](https://docs.astral.sh/uv/) must be installed.
Install it with: `curl -LsSf https://astral.sh/uv/install.sh | sh`

## Available scripts

- **`scripts/ods.py`** — All ODS operations via subcommands (see below).

Run `uv run scripts/ods.py --help` for the full command list, or
`uv run scripts/ods.py <command> --help` for per-command usage.

## Commands

| Command | What it does |
|---|---|
| `file-info <file>` | Sheet names, row/col counts — start here when exploring a file |
| `list-sheets <file>` | Sheet names only |
| `read-sheet <file> --sheet NAME` | All rows as JSON; supports `--offset N` and `--limit N` |
| `get-cell <file> --sheet NAME --cell A1` | Single cell value |
| `set-cell <file> --sheet NAME --cell A1 --value V [--type float\|string\|bool]` | Set a cell |
| `append-rows <file> --sheet NAME --rows JSON` | Append rows |
| `create <file> [--sheets S1 S2 …] [--overwrite]` | Create a new ODS file |
| `add-sheet <file> --sheet NAME` | Add a sheet |
| `rename-sheet <file> --sheet OLD --new-name NEW` | Rename a sheet |
| `delete-sheet <file> --sheet NAME --confirm` | Delete a sheet |

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Invalid arguments |
| 2 | File not found |
| 3 | Sheet not found |
| 5 | ODF parse or write error |

## Gotchas

- **Always use `uv run`** — invoke as `uv run scripts/ods.py <command>`, never `python scripts/ods.py`. Running with plain Python will fail because dependencies are declared as PEP 723 inline metadata and installed by uv.
- **`set-cell` discards formatting** — it rebuilds the sheet element, so cell-level formatting (fonts, colours, borders) is not preserved. Formulas are also replaced by their last computed values.
- **`create` fails if the file exists** — pass `--overwrite` only after confirming with the user. Omitting it when the file is present raises an error (exit code 1), which is the safe default.
- **`delete-sheet --confirm` is irreversible** — always verify with the user before passing this flag.

## Workflow guidance

**Exploring a file** — always run `file-info` first to understand the
structure, then `read-sheet` for data. For large sheets use `--limit` and
`--offset` to page through rows rather than reading everything at once.

**Writing data** — `append-rows` is efficient for adding multiple rows. `set-cell` is fine for single updates (see Gotchas for formatting caveats).

**Destructive operations** — confirm with the user before passing `--confirm` to `delete-sheet` or `--overwrite` to `create`.

## Examples

```bash
# Explore a file
uv run scripts/ods.py file-info data.ods

# Read the first 20 rows of a sheet
uv run scripts/ods.py read-sheet data.ods --sheet "Sales" --limit 20

# Read rows 20–39 (second page)
uv run scripts/ods.py read-sheet data.ods --sheet "Sales" --offset 20 --limit 20

# Get a cell
uv run scripts/ods.py get-cell data.ods --sheet "Sales" --cell B3

# Set a numeric cell
uv run scripts/ods.py set-cell data.ods --sheet "Sales" --cell B3 --value 42 --type float

# Append rows
uv run scripts/ods.py append-rows data.ods --sheet "Sales" --rows '[["Alice", 1200], ["Bob", 950]]'

# Create a new file with two sheets
uv run scripts/ods.py create report.ods --sheets "Summary" "Data"

# Rename a sheet
uv run scripts/ods.py rename-sheet data.ods --sheet "Sheet1" --new-name "Sales"

# Delete a sheet (ask user before passing --confirm)
uv run scripts/ods.py delete-sheet data.ods --sheet "Scratch" --confirm
```
