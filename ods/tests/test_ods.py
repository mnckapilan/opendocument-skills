import json
import tempfile
from pathlib import Path

import pytest

from .conftest import run


# ── create ────────────────────────────────────────────────────────────────────

class TestCreate:
    def test_default_sheet(self, tmp_path):
        path = str(tmp_path / "out.ods")
        code, data, _ = run("create", path)
        assert code == 0
        assert data["sheets"] == ["Sheet1"]
        assert Path(path).exists()

    def test_custom_sheets(self, tmp_path):
        path = str(tmp_path / "out.ods")
        code, data, _ = run("create", path, "--sheets", "Income", "Expenses")
        assert code == 0
        assert data["sheets"] == ["Income", "Expenses"]

    def test_fails_if_exists(self, empty_file):
        code, _, stderr = run("create", empty_file)
        assert code == 1
        assert "already exists" in stderr

    def test_overwrite(self, empty_file):
        code, data, _ = run("create", empty_file, "--overwrite", "--sheets", "New")
        assert code == 0
        assert data["sheets"] == ["New"]


# ── list-sheets ───────────────────────────────────────────────────────────────

class TestListSheets:
    def test_lists_all_sheets(self, empty_file):
        code, data, _ = run("list-sheets", empty_file)
        assert code == 0
        assert data["sheets"] == ["Sales", "Summary"]
        assert data["count"] == 2

    def test_file_not_found(self, tmp_path):
        code, _, stderr = run("list-sheets", str(tmp_path / "missing.ods"))
        assert code == 2
        assert "not found" in stderr.lower()


# ── file-info ─────────────────────────────────────────────────────────────────

class TestFileInfo:
    def test_empty_sheets(self, empty_file):
        code, data, _ = run("file-info", empty_file)
        assert code == 0
        assert data["sheet_count"] == 2
        sheets = {s["name"]: s for s in data["sheets"]}
        assert sheets["Sales"]["rows"] == 0
        assert sheets["Sales"]["cols"] == 0

    def test_with_data(self, data_file):
        code, data, _ = run("file-info", data_file)
        assert code == 0
        sheets = {s["name"]: s for s in data["sheets"]}
        assert sheets["Sales"]["rows"] == 4
        assert sheets["Sales"]["cols"] == 3


# ── read-sheet ────────────────────────────────────────────────────────────────

class TestReadSheet:
    def test_reads_all_rows(self, data_file):
        code, data, _ = run("read-sheet", data_file, "--sheet", "Sales")
        assert code == 0
        assert data["total_rows"] == 4
        assert data["rows"][0] == ["Name", "Q1", "Q2"]
        assert data["rows"][1] == ["Alice", 1200, 1400]

    def test_limit(self, data_file):
        code, data, _ = run("read-sheet", data_file, "--sheet", "Sales", "--limit", "2")
        assert code == 0
        assert data["returned"] == 2
        assert data["total_rows"] == 4

    def test_offset(self, data_file):
        code, data, _ = run("read-sheet", data_file, "--sheet", "Sales", "--offset", "1")
        assert code == 0
        assert data["offset"] == 1
        assert data["rows"][0] == ["Alice", 1200, 1400]

    def test_offset_and_limit(self, data_file):
        code, data, _ = run("read-sheet", data_file, "--sheet", "Sales", "--offset", "1", "--limit", "2")
        assert code == 0
        assert data["returned"] == 2
        assert data["rows"][0] == ["Alice", 1200, 1400]
        assert data["rows"][1] == ["Bob", 950, 1100]

    def test_empty_sheet(self, empty_file):
        code, data, _ = run("read-sheet", empty_file, "--sheet", "Sales")
        assert code == 0
        assert data["rows"] == []
        assert data["total_rows"] == 0

    def test_sheet_not_found(self, empty_file):
        code, _, stderr = run("read-sheet", empty_file, "--sheet", "NoSuch")
        assert code == 3
        assert "NoSuch" in stderr


# ── get-cell ──────────────────────────────────────────────────────────────────

class TestGetCell:
    def test_string_cell(self, data_file):
        code, data, _ = run("get-cell", data_file, "--sheet", "Sales", "--cell", "A1")
        assert code == 0
        assert data["value"] == "Name"

    def test_numeric_cell(self, data_file):
        code, data, _ = run("get-cell", data_file, "--sheet", "Sales", "--cell", "B2")
        assert code == 0
        assert data["value"] == 1200

    def test_out_of_bounds_row(self, data_file):
        code, data, _ = run("get-cell", data_file, "--sheet", "Sales", "--cell", "A99")
        assert code == 0
        assert data["value"] is None

    def test_out_of_bounds_col(self, data_file):
        code, data, _ = run("get-cell", data_file, "--sheet", "Sales", "--cell", "Z1")
        assert code == 0
        assert data["value"] is None

    def test_invalid_cell_ref(self, data_file):
        code, _, stderr = run("get-cell", data_file, "--sheet", "Sales", "--cell", "notacell")
        assert code == 1
        assert "invalid cell reference" in stderr.lower()


# ── set-cell ──────────────────────────────────────────────────────────────────

class TestSetCell:
    def test_set_string(self, data_file):
        code, data, _ = run("set-cell", data_file, "--sheet", "Sales", "--cell", "A1", "--value", "Rep")
        assert code == 0
        assert data["value"] == "Rep"
        _, read, _ = run("get-cell", data_file, "--sheet", "Sales", "--cell", "A1")
        assert read["value"] == "Rep"

    def test_set_float(self, data_file):
        code, data, _ = run("set-cell", data_file, "--sheet", "Sales", "--cell", "B2",
                             "--value", "9999", "--type", "float")
        assert code == 0
        assert data["value"] == 9999.0
        _, read, _ = run("get-cell", data_file, "--sheet", "Sales", "--cell", "B2")
        assert read["value"] == 9999

    def test_set_bool(self, data_file):
        code, data, _ = run("set-cell", data_file, "--sheet", "Sales", "--cell", "A1",
                             "--value", "true", "--type", "bool")
        assert code == 0
        assert data["value"] is True

    def test_set_expands_rows(self, empty_file):
        code, _, _ = run("set-cell", empty_file, "--sheet", "Sales", "--cell", "C5",
                         "--value", "hello")
        assert code == 0
        _, read, _ = run("get-cell", empty_file, "--sheet", "Sales", "--cell", "C5")
        assert read["value"] == "hello"

    def test_set_invalid_float(self, data_file):
        code, _, stderr = run("set-cell", data_file, "--sheet", "Sales", "--cell", "B2",
                               "--value", "notanumber", "--type", "float")
        assert code == 1
        assert "cannot convert" in stderr.lower()

    def test_existing_rows_preserved(self, data_file):
        run("set-cell", data_file, "--sheet", "Sales", "--cell", "B2", "--value", "1", "--type", "float")
        _, data, _ = run("read-sheet", data_file, "--sheet", "Sales")
        assert data["total_rows"] == 4
        assert data["rows"][2][0] == "Bob"


# ── append-rows ───────────────────────────────────────────────────────────────

class TestAppendRows:
    def test_appends_rows(self, data_file):
        new_rows = json.dumps([["Dave", 700, 800]])
        code, data, _ = run("append-rows", data_file, "--sheet", "Sales", "--rows", new_rows)
        assert code == 0
        assert data["rows_added"] == 1
        _, read, _ = run("read-sheet", data_file, "--sheet", "Sales")
        assert read["total_rows"] == 5
        assert read["rows"][-1][0] == "Dave"

    def test_appends_multiple(self, empty_file):
        rows = json.dumps([["A", 1], ["B", 2], ["C", 3]])
        code, data, _ = run("append-rows", empty_file, "--sheet", "Sales", "--rows", rows)
        assert code == 0
        assert data["rows_added"] == 3

    def test_invalid_json(self, empty_file):
        code, _, stderr = run("append-rows", empty_file, "--sheet", "Sales", "--rows", "notjson")
        assert code == 1
        assert "invalid json" in stderr.lower()

    def test_non_array_rows(self, empty_file):
        code, _, stderr = run("append-rows", empty_file, "--sheet", "Sales", "--rows", '{"key": "val"}')
        assert code == 1


# ── add-sheet ─────────────────────────────────────────────────────────────────

class TestAddSheet:
    def test_adds_sheet(self, empty_file):
        code, data, _ = run("add-sheet", empty_file, "--sheet", "Notes")
        assert code == 0
        _, sheets, _ = run("list-sheets", empty_file)
        assert "Notes" in sheets["sheets"]

    def test_duplicate_fails(self, empty_file):
        code, _, stderr = run("add-sheet", empty_file, "--sheet", "Sales")
        assert code == 3
        assert "already exists" in stderr


# ── rename-sheet ──────────────────────────────────────────────────────────────

class TestRenameSheet:
    def test_renames(self, empty_file):
        code, data, _ = run("rename-sheet", empty_file, "--sheet", "Summary", "--new-name", "Overview")
        assert code == 0
        _, sheets, _ = run("list-sheets", empty_file)
        assert "Overview" in sheets["sheets"]
        assert "Summary" not in sheets["sheets"]

    def test_source_not_found(self, empty_file):
        code, _, stderr = run("rename-sheet", empty_file, "--sheet", "NoSuch", "--new-name", "X")
        assert code == 3

    def test_target_already_exists(self, empty_file):
        code, _, stderr = run("rename-sheet", empty_file, "--sheet", "Sales", "--new-name", "Summary")
        assert code == 3
        assert "already exists" in stderr


# ── delete-sheet ──────────────────────────────────────────────────────────────

class TestDeleteSheet:
    def test_requires_confirm(self, empty_file):
        code, _, stderr = run("delete-sheet", empty_file, "--sheet", "Summary")
        assert code == 1
        assert "--confirm" in stderr

    def test_deletes_sheet(self, empty_file):
        code, data, _ = run("delete-sheet", empty_file, "--sheet", "Summary", "--confirm")
        assert code == 0
        _, sheets, _ = run("list-sheets", empty_file)
        assert "Summary" not in sheets["sheets"]

    def test_cannot_delete_last_sheet(self, tmp_path):
        path = str(tmp_path / "single.ods")
        run("create", path)
        code, _, stderr = run("delete-sheet", path, "--sheet", "Sheet1", "--confirm")
        assert code == 1
        assert "only sheet" in stderr

    def test_sheet_not_found(self, empty_file):
        code, _, stderr = run("delete-sheet", empty_file, "--sheet", "NoSuch", "--confirm")
        assert code == 3
