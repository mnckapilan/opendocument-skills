import json
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "scripts" / "odt.py"


def run(*args):
    """Run odt.py with the given args. Returns (exit_code, data, stderr)."""
    result = subprocess.run(
        ["uv", "run", str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )
    stdout = result.stdout.strip()
    try:
        data = json.loads(stdout) if stdout else None
    except json.JSONDecodeError:
        data = stdout
    return result.returncode, data, result.stderr


@pytest.fixture
def empty_doc(tmp_path):
    path = str(tmp_path / "test.odt")
    code, _, _ = run("create", path)
    assert code == 0
    return path


@pytest.fixture
def doc_with_content(empty_doc):
    """Five blocks: h1, p, p, h2, p."""
    run("append-paragraph", empty_doc, "--text", "Introduction", "--style", "h1")
    run("append-paragraph", empty_doc, "--text", "This is the first paragraph.")
    run("append-paragraph", empty_doc, "--text", "This is the second paragraph.")
    run("append-paragraph", empty_doc, "--text", "Chapter Two", "--style", "h2")
    run("append-paragraph", empty_doc, "--text", "More content here.")
    return empty_doc
