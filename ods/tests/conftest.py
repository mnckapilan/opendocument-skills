import json
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "scripts" / "ods.py"


def run(*args):
    """Run ods.py with the given args. Returns (exit_code, data, stderr)."""
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
def empty_file(tmp_path):
    path = str(tmp_path / "test.ods")
    code, _, _ = run("create", path, "--sheets", "Sales", "Summary")
    assert code == 0
    return path


@pytest.fixture
def data_file(empty_file):
    rows = json.dumps([
        ["Name", "Q1", "Q2"],
        ["Alice", 1200, 1400],
        ["Bob", 950, 1100],
        ["Carol", 1600, 1800],
    ])
    code, _, _ = run("append-rows", empty_file, "--sheet", "Sales", "--rows", rows)
    assert code == 0
    return empty_file
