# odf-skills

Agent skills for working with [OpenDocument Format](https://en.wikipedia.org/wiki/OpenDocument) files — the open standard behind LibreOffice, Google Docs exports, and more.

Skills follow the [Agent Skills](https://agentskills.io) open standard and work with any compatible agent.

## Skills

### `ods` — OpenDocument Spreadsheet

Read and write `.ods` spreadsheet files. Supports exploring files, reading rows with pagination, getting and setting cells, appending rows, and managing sheets (create, add, rename, delete).

## Installation

Requires [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`).

```bash
git clone https://github.com/mnckapilan/odf-skills
cp -r odf-skills/ods ~/.claude/skills/ods
```

Then invoke with `/ods` in your agent.

## Caveats

- `set-cell` rebuilds the sheet element — cell-level formatting (fonts, colours, borders) is not preserved
- Formulas are replaced by their last computed values when a sheet is rebuilt
