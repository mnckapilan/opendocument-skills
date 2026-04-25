# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A collection of Claude Code skills for working with ODF (OpenDocument Format) files. Each skill lives in its own subdirectory and can be installed by copying that directory to `~/.claude/skills/<name>/`.

Current skills: `ods/` (OpenDocument Spreadsheet).

## Running tests

```bash
# All tests
uv run --with pytest pytest ods/tests/ -v

# Single test
uv run --with pytest pytest ods/tests/test_ods.py::TestReadSheet::test_limit -v
```

Tests require `uv` in PATH. No other setup needed — odfpy is declared as an inline dependency in the script and installed automatically.

## Skill structure

Each skill directory follows this layout:

```
<format>/
├── SKILL.md          # Frontmatter + instructions loaded by Claude Code
├── scripts/
│   └── <format>.py  # Self-contained CLI script (PEP 723 inline deps, run via uv)
├── evals/
│   ├── evals.json   # Eval test cases (prompts, expected outputs, assertions)
│   └── files/       # Committed ODS/ODF fixture files for evals
└── tests/
    ├── conftest.py  # Shared fixtures (create temp ODS files via the script itself)
    └── test_<format>.py
```

## Scripts

Scripts are self-contained via [PEP 723](https://peps.python.org/pep-0723/) inline dependency declarations and run with `uv run`. Always invoke as `uv run scripts/<format>.py <command>`, never `python scripts/<format>.py`.

All commands output JSON to stdout and errors to stderr. Exit codes: 0 success, 1 invalid args, 2 file not found, 3 sheet not found, 5 ODF error.

### odfpy attribute API

odfpy's `getAttribute`/`setAttribute` accept lowercase hyphen-stripped names, not namespace-prefixed strings:
- `"valuetype"` not `"office:value-type"`
- `"numbercolumnsrepeated"` not `"table:number-columns-repeated"`
- `"name"` not `"table:name"` (on Table elements)

Direct dict access (`element.attributes[ns_tuple]`) works but bypasses grammar validation — prefer the string API.

## Tests vs evals

**Tests** (`tests/`) are deterministic CI tests for the script CLI. Each test creates fresh ODS files via `tmp_path` fixtures and checks exact JSON output and exit codes.

**Evals** (`evals/`) assess skill quality — does Claude use the script correctly given realistic user prompts? These require spawning Claude with/without the skill and an LLM judge to grade assertions. Results go in `ods-workspace/` (gitignored). Not wired into CI.

## Adding a new skill

1. Create `<format>/` with the structure above
2. Add `<format>-workspace/` to `.gitignore`
3. Add a test job to `.github/workflows/test.yml`
