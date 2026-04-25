# odf-skills

Agent skills for working with [OpenDocument Format](https://en.wikipedia.org/wiki/OpenDocument) files — the open standard behind LibreOffice, Google Docs exports, and more.

Skills follow the [Agent Skills](https://agentskills.io) open standard and work with any compatible agent.

## Skills

### `ods` — OpenDocument Spreadsheet

Read and write `.ods` spreadsheet files. Supports exploring files, reading rows with pagination, getting and setting cells, appending rows, and managing sheets (create, add, rename, delete).

### `odt` — OpenDocument Text

Read and write `.odt` document files. Supports exploring documents, reading paragraphs and headings by index, appending and inserting content, replacing text in place, listing headings, and find-and-replace across the whole document.

## Installation

Requires [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`).

```bash
git clone https://github.com/mnckapilan/odf-skills

# Install one or both skills
cp -r odf-skills/ods ~/.claude/skills/ods
cp -r odf-skills/odt ~/.claude/skills/odt
```

Then invoke with `/ods` or `/odt` in your agent.

## Caveats

- **ods** — `set-cell` rebuilds the sheet element; cell-level formatting and formulas are not preserved
- **odt** — `set-paragraph` and `find-replace` rebuild modified blocks; inline formatting (bold, italic, etc.) within changed blocks is not preserved
