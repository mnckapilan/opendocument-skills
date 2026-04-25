from pathlib import Path

import pytest

from .conftest import run


# ── create ────────────────────────────────────────────────────────────────────

class TestCreate:
    def test_creates_empty_file(self, tmp_path):
        path = str(tmp_path / "out.odt")
        code, data, _ = run("create", path)
        assert code == 0
        assert data["success"] is True
        assert Path(path).exists()

    def test_sets_title(self, tmp_path):
        path = str(tmp_path / "out.odt")
        code, data, _ = run("create", path, "--title", "My Doc")
        assert code == 0
        assert data["title"] == "My Doc"

    def test_fails_if_exists(self, empty_doc):
        code, _, stderr = run("create", empty_doc)
        assert code == 1
        assert "already exists" in stderr

    def test_overwrite(self, empty_doc):
        code, data, _ = run("create", empty_doc, "--overwrite")
        assert code == 0
        assert data["success"] is True


# ── file-info ─────────────────────────────────────────────────────────────────

class TestFileInfo:
    def test_empty_document(self, empty_doc):
        code, data, _ = run("file-info", empty_doc)
        assert code == 0
        assert data["total_blocks"] == 0
        assert data["paragraphs"] == 0
        assert data["headings"] == 0
        assert data["words"] == 0

    def test_with_content(self, doc_with_content):
        code, data, _ = run("file-info", doc_with_content)
        assert code == 0
        assert data["total_blocks"] == 5
        assert data["paragraphs"] == 3
        assert data["headings"] == 2
        assert data["words"] > 0

    def test_file_not_found(self, tmp_path):
        code, _, stderr = run("file-info", str(tmp_path / "missing.odt"))
        assert code == 2
        assert "not found" in stderr.lower()


# ── read-text ─────────────────────────────────────────────────────────────────

class TestReadText:
    def test_reads_all_blocks(self, doc_with_content):
        code, data, _ = run("read-text", doc_with_content)
        assert code == 0
        assert data["total"] == 5
        assert data["returned"] == 5
        assert data["blocks"][0]["type"] == "heading"
        assert data["blocks"][0]["text"] == "Introduction"
        assert data["blocks"][0]["level"] == 1

    def test_limit(self, doc_with_content):
        code, data, _ = run("read-text", doc_with_content, "--limit", "2")
        assert code == 0
        assert data["returned"] == 2
        assert data["total"] == 5

    def test_offset(self, doc_with_content):
        code, data, _ = run("read-text", doc_with_content, "--offset", "1")
        assert code == 0
        assert data["offset"] == 1
        assert data["blocks"][0]["text"] == "This is the first paragraph."

    def test_offset_and_limit(self, doc_with_content):
        code, data, _ = run("read-text", doc_with_content, "--offset", "1", "--limit", "2")
        assert code == 0
        assert data["returned"] == 2
        assert data["blocks"][0]["text"] == "This is the first paragraph."
        assert data["blocks"][1]["text"] == "This is the second paragraph."

    def test_empty_document(self, empty_doc):
        code, data, _ = run("read-text", empty_doc)
        assert code == 0
        assert data["total"] == 0
        assert data["blocks"] == []


# ── get-paragraph ─────────────────────────────────────────────────────────────

class TestGetParagraph:
    def test_get_heading(self, doc_with_content):
        code, data, _ = run("get-paragraph", doc_with_content, "--index", "0")
        assert code == 0
        assert data["type"] == "heading"
        assert data["level"] == 1
        assert data["text"] == "Introduction"

    def test_get_paragraph(self, doc_with_content):
        code, data, _ = run("get-paragraph", doc_with_content, "--index", "1")
        assert code == 0
        assert data["type"] == "paragraph"
        assert data["text"] == "This is the first paragraph."

    def test_index_out_of_range(self, doc_with_content):
        code, _, stderr = run("get-paragraph", doc_with_content, "--index", "99")
        assert code == 3
        assert "out of range" in stderr.lower()

    def test_empty_document_out_of_range(self, empty_doc):
        code, _, stderr = run("get-paragraph", empty_doc, "--index", "0")
        assert code == 3


# ── set-paragraph ─────────────────────────────────────────────────────────────

class TestSetParagraph:
    def test_replaces_text(self, doc_with_content):
        code, data, _ = run("set-paragraph", doc_with_content, "--index", "1",
                             "--text", "Replaced paragraph.")
        assert code == 0
        assert data["success"] is True
        _, read, _ = run("get-paragraph", doc_with_content, "--index", "1")
        assert read["text"] == "Replaced paragraph."

    def test_preserves_heading_type(self, doc_with_content):
        run("set-paragraph", doc_with_content, "--index", "0", "--text", "New Title")
        _, read, _ = run("get-paragraph", doc_with_content, "--index", "0")
        assert read["type"] == "heading"
        assert read["level"] == 1
        assert read["text"] == "New Title"

    def test_changes_style_to_heading(self, doc_with_content):
        run("set-paragraph", doc_with_content, "--index", "1",
            "--text", "Now a heading", "--style", "h3")
        _, read, _ = run("get-paragraph", doc_with_content, "--index", "1")
        assert read["type"] == "heading"
        assert read["level"] == 3

    def test_other_blocks_untouched(self, doc_with_content):
        run("set-paragraph", doc_with_content, "--index", "1", "--text", "Changed.")
        _, data, _ = run("read-text", doc_with_content)
        assert data["total"] == 5
        assert data["blocks"][2]["text"] == "This is the second paragraph."

    def test_index_out_of_range(self, doc_with_content):
        code, _, stderr = run("set-paragraph", doc_with_content, "--index", "99",
                               "--text", "x")
        assert code == 3


# ── append-paragraph ──────────────────────────────────────────────────────────

class TestAppendParagraph:
    def test_appends_paragraph(self, doc_with_content):
        code, data, _ = run("append-paragraph", doc_with_content, "--text", "Appended.")
        assert code == 0
        assert data["index"] == 5
        _, read, _ = run("read-text", doc_with_content)
        assert read["total"] == 6
        assert read["blocks"][-1]["text"] == "Appended."

    def test_appends_heading(self, doc_with_content):
        code, data, _ = run("append-paragraph", doc_with_content,
                             "--text", "Conclusion", "--style", "h1")
        assert code == 0
        _, block, _ = run("get-paragraph", doc_with_content, "--index", str(data["index"]))
        assert block["type"] == "heading"
        assert block["level"] == 1

    def test_appends_to_empty_doc(self, empty_doc):
        code, data, _ = run("append-paragraph", empty_doc, "--text", "First line.")
        assert code == 0
        assert data["index"] == 0
        _, read, _ = run("read-text", empty_doc)
        assert read["total"] == 1


# ── insert-paragraph ──────────────────────────────────────────────────────────

class TestInsertParagraph:
    def test_inserts_at_position(self, doc_with_content):
        code, data, _ = run("insert-paragraph", doc_with_content,
                             "--index", "1", "--text", "Inserted.")
        assert code == 0
        assert data["index"] == 1
        _, read, _ = run("read-text", doc_with_content)
        assert read["total"] == 6
        assert read["blocks"][1]["text"] == "Inserted."
        assert read["blocks"][2]["text"] == "This is the first paragraph."

    def test_insert_beyond_end_appends(self, doc_with_content):
        code, data, _ = run("insert-paragraph", doc_with_content,
                             "--index", "999", "--text", "At end.")
        assert code == 0
        _, read, _ = run("read-text", doc_with_content)
        assert read["blocks"][-1]["text"] == "At end."

    def test_insert_at_zero(self, doc_with_content):
        run("insert-paragraph", doc_with_content, "--index", "0", "--text", "Preamble.")
        _, read, _ = run("read-text", doc_with_content)
        assert read["blocks"][0]["text"] == "Preamble."
        assert read["blocks"][1]["text"] == "Introduction"


# ── delete-paragraph ──────────────────────────────────────────────────────────

class TestDeleteParagraph:
    def test_requires_confirm(self, doc_with_content):
        code, _, stderr = run("delete-paragraph", doc_with_content, "--index", "1")
        assert code == 1
        assert "--confirm" in stderr

    def test_deletes_block(self, doc_with_content):
        code, data, _ = run("delete-paragraph", doc_with_content,
                             "--index", "1", "--confirm")
        assert code == 0
        assert data["deleted_index"] == 1
        assert data["deleted_text"] == "This is the first paragraph."
        _, read, _ = run("read-text", doc_with_content)
        assert read["total"] == 4
        assert read["blocks"][1]["text"] == "This is the second paragraph."

    def test_index_out_of_range(self, doc_with_content):
        code, _, stderr = run("delete-paragraph", doc_with_content,
                               "--index", "99", "--confirm")
        assert code == 3

    def test_delete_from_empty(self, empty_doc):
        code, _, _ = run("delete-paragraph", empty_doc, "--index", "0", "--confirm")
        assert code == 3


# ── list-headings ─────────────────────────────────────────────────────────────

class TestListHeadings:
    def test_lists_headings(self, doc_with_content):
        code, data, _ = run("list-headings", doc_with_content)
        assert code == 0
        assert data["count"] == 2
        h = data["headings"]
        assert h[0] == {"index": 0, "level": 1, "text": "Introduction"}
        assert h[1] == {"index": 3, "level": 2, "text": "Chapter Two"}

    def test_empty_document(self, empty_doc):
        code, data, _ = run("list-headings", empty_doc)
        assert code == 0
        assert data["count"] == 0
        assert data["headings"] == []


# ── find-replace ──────────────────────────────────────────────────────────────

class TestFindReplace:
    def test_replaces_text(self, doc_with_content):
        code, data, _ = run("find-replace", doc_with_content,
                             "--find", "first", "--replace", "1st")
        assert code == 0
        assert data["replacements"] == 1
        _, block, _ = run("get-paragraph", doc_with_content, "--index", "1")
        assert "1st" in block["text"]

    def test_dry_run_no_change(self, doc_with_content):
        code, data, _ = run("find-replace", doc_with_content,
                             "--find", "first", "--replace", "1st", "--dry-run")
        assert code == 0
        assert data["dry_run"] is True
        assert data["matches"] == 1
        _, block, _ = run("get-paragraph", doc_with_content, "--index", "1")
        assert "first" in block["text"]

    def test_no_matches(self, doc_with_content):
        code, data, _ = run("find-replace", doc_with_content,
                             "--find", "xyznotfound", "--replace", "x")
        assert code == 0
        assert data["replacements"] == 0

    def test_replaces_across_multiple_blocks(self, doc_with_content):
        run("append-paragraph", doc_with_content, "--text", "first mention again.")
        code, data, _ = run("find-replace", doc_with_content,
                             "--find", "first", "--replace", "FIRST")
        assert code == 0
        assert data["replacements"] == 2
