# /// script
# requires-python = ">=3.11"
# dependencies = ["odfpy>=1.4.1"]
# ///

"""
Read and write ODT (OpenDocument Text) files.

Exit codes:
  0  success
  1  invalid arguments
  2  file not found
  3  block index out of range
  5  ODF parse / write error
"""

import argparse
import json
import sys
from pathlib import Path


# ── output helpers ────────────────────────────────────────────────────────────

def die(msg: str, code: int = 1) -> None:
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(code)


def emit(data: object) -> None:
    print(json.dumps(data, ensure_ascii=False))
    sys.exit(0)


# ── document helpers ──────────────────────────────────────────────────────────

def load_doc(path: str):
    from odf.opendocument import load  # type: ignore[import]
    p = Path(path)
    if not p.exists():
        die(f"File not found: {path}", code=2)
    try:
        return load(str(p))
    except Exception as exc:
        die(f"Failed to open ODT file: {exc}", code=5)


def save_doc(doc, path: str) -> None:
    try:
        doc.save(path)
    except Exception as exc:
        die(f"Failed to save ODT file: {exc}", code=5)


# ── text / element helpers ────────────────────────────────────────────────────

# odfpy P and H are factory functions, not classes; identify by qualified name.
from odf.namespaces import TEXTNS as _TEXTNS  # type: ignore[import]
_P_QNAME = (_TEXTNS, 'p')
_H_QNAME = (_TEXTNS, 'h')


def _is_heading(elem) -> bool:
    return getattr(elem, 'qname', None) == _H_QNAME


def _is_content_block(elem) -> bool:
    q = getattr(elem, 'qname', None)
    return q == _P_QNAME or q == _H_QNAME


def get_text(elem) -> str:
    """Recursively extract plain text from an element."""
    parts = []
    for node in getattr(elem, 'childNodes', []):
        if hasattr(node, 'data'):
            parts.append(node.data)
        else:
            parts.append(get_text(node))
    return ''.join(parts)


def get_content_elements(doc) -> list:
    """Return all direct P/H children of doc.text."""
    return [e for e in doc.text.childNodes if _is_content_block(e)]


def elem_to_dict(elem, index: int) -> dict:
    d: dict = {"index": index, "text": get_text(elem)}
    if _is_heading(elem):
        d["type"] = "heading"
        d["level"] = int(elem.getAttribute("outlinelevel") or 1)
    else:
        d["type"] = "paragraph"
        style = elem.getAttribute("stylename")
        if style:
            d["style"] = style
    return d


# Maps user-facing style names to (kind, param) where:
#   kind="heading" → H(outlinelevel=param)
#   kind="paragraph", param=name → P(stylename=name)
#   kind="paragraph", param=None → P()
_STYLE_MAP: dict[str, tuple[str, object]] = {
    "h1": ("heading", 1), "heading1": ("heading", 1),
    "h2": ("heading", 2), "heading2": ("heading", 2),
    "h3": ("heading", 3), "heading3": ("heading", 3),
    "h4": ("heading", 4), "heading4": ("heading", 4),
    "h5": ("heading", 5), "heading5": ("heading", 5),
    "h6": ("heading", 6), "heading6": ("heading", 6),
    "title":    ("paragraph", "Title"),
    "subtitle": ("paragraph", "Subtitle"),
    "default":  ("paragraph", None),
    "body":     ("paragraph", None),
}


def make_element(text: str, style: str = "default"):
    from odf.text import P, H  # type: ignore[import]
    key = (style or "default").lower()
    if key in _STYLE_MAP:
        kind, param = _STYLE_MAP[key]
        if kind == "heading":
            return H(outlinelevel=param, text=text)
        return P(stylename=param, text=text) if param else P(text=text)
    # Unknown style: use as a named paragraph style.
    return P(stylename=style, text=text)


def clone_with_text(old_elem, new_text: str):
    """Rebuild an element preserving its type/style but replacing text content."""
    from odf.text import P, H  # type: ignore[import]
    if _is_heading(old_elem):
        level = int(old_elem.getAttribute("outlinelevel") or 1)
        return H(outlinelevel=level, text=new_text)
    style = old_elem.getAttribute("stylename")
    return P(stylename=style, text=new_text) if style else P(text=new_text)


def count_words(elems) -> int:
    text = ' '.join(get_text(e) for e in elems)
    return len(text.split()) if text.strip() else 0


def get_meta_title(doc) -> str | None:
    try:
        for elem in doc.meta.childNodes:
            if hasattr(elem, 'qname') and elem.qname[1] == 'title':
                t = get_text(elem)
                return t or None
    except Exception:
        pass
    return None


def set_meta_title(doc, title: str) -> None:
    from odf import dc  # type: ignore[import]
    t = dc.Title()
    t.addText(title)
    doc.meta.addElement(t)


def require_index(elems: list, idx: int) -> None:
    if idx < 0 or idx >= len(elems):
        n = len(elems)
        die(
            f"Index {idx} out of range. "
            f"Document has {n} block{'s' if n != 1 else ''}"
            + (f" (0–{n - 1})" if n else "") + ".",
            code=3,
        )


# ── commands ──────────────────────────────────────────────────────────────────

def cmd_create(args) -> None:
    from odf.opendocument import OpenDocumentText  # type: ignore[import]
    p = Path(args.file)
    if p.exists() and not args.overwrite:
        die(f"File already exists: {args.file}. Use --overwrite to replace it.")
    doc = OpenDocumentText()
    if args.title:
        set_meta_title(doc, args.title)
    save_doc(doc, str(p))
    result: dict = {"success": True, "path": str(p.resolve())}
    if args.title:
        result["title"] = args.title
    emit(result)


def cmd_file_info(args) -> None:
    doc = load_doc(args.file)
    elems = get_content_elements(doc)
    heading_count = sum(1 for e in elems if _is_heading(e))
    emit({
        "path": str(Path(args.file).resolve()),
        "title": get_meta_title(doc),
        "paragraphs": len(elems) - heading_count,
        "headings": heading_count,
        "total_blocks": len(elems),
        "words": count_words(elems),
    })


def cmd_read_text(args) -> None:
    doc = load_doc(args.file)
    elems = get_content_elements(doc)
    total = len(elems)
    offset = args.offset
    page = elems[offset : offset + args.limit] if args.limit else elems[offset:]
    emit({
        "total": total,
        "offset": offset,
        "returned": len(page),
        "blocks": [elem_to_dict(e, offset + i) for i, e in enumerate(page)],
    })


def cmd_get_paragraph(args) -> None:
    doc = load_doc(args.file)
    elems = get_content_elements(doc)
    require_index(elems, args.index)
    emit(elem_to_dict(elems[args.index], args.index))


def cmd_set_paragraph(args) -> None:
    doc = load_doc(args.file)
    elems = get_content_elements(doc)
    idx = args.index
    require_index(elems, idx)
    old = elems[idx]
    new = make_element(args.text, args.style) if args.style else clone_with_text(old, args.text)
    doc.text.insertBefore(new, old)
    doc.text.removeChild(old)
    save_doc(doc, args.file)
    emit({"success": True, "index": idx, "text": args.text})


def cmd_append_paragraph(args) -> None:
    doc = load_doc(args.file)
    elems = get_content_elements(doc)
    new = make_element(args.text, args.style or "default")
    doc.text.addElement(new)
    save_doc(doc, args.file)
    emit({"success": True, "index": len(elems), "text": args.text})


def cmd_insert_paragraph(args) -> None:
    doc = load_doc(args.file)
    elems = get_content_elements(doc)
    idx = args.index
    new = make_element(args.text, args.style or "default")
    if idx >= len(elems):
        doc.text.addElement(new)
        actual_idx = len(elems)
    else:
        doc.text.insertBefore(new, elems[idx])
        actual_idx = idx
    save_doc(doc, args.file)
    emit({"success": True, "index": actual_idx, "text": args.text})


def cmd_delete_paragraph(args) -> None:
    if not args.confirm:
        die("--confirm is required to delete a block. This cannot be undone.")
    doc = load_doc(args.file)
    elems = get_content_elements(doc)
    idx = args.index
    require_index(elems, idx)
    old = elems[idx]
    text = get_text(old)
    doc.text.removeChild(old)
    save_doc(doc, args.file)
    emit({"success": True, "deleted_index": idx, "deleted_text": text})


def cmd_list_headings(args) -> None:
    doc = load_doc(args.file)
    elems = get_content_elements(doc)
    headings = [
        {"index": i, "level": int(e.getAttribute("outlinelevel") or 1), "text": get_text(e)}
        for i, e in enumerate(elems)
        if _is_heading(e)
    ]
    emit({"headings": headings, "count": len(headings)})


def cmd_find_replace(args) -> None:
    doc = load_doc(args.file)
    elems = get_content_elements(doc)
    find_str, replace_str = args.find, args.replace

    changes = [
        (i, elem, get_text(elem), get_text(elem).replace(find_str, replace_str))
        for i, elem in enumerate(elems)
        if find_str in get_text(elem)
    ]

    if args.dry_run:
        emit({
            "dry_run": True,
            "matches": len(changes),
            "changes": [{"index": i, "old": old, "new": new} for i, _, old, new in changes],
        })

    for _, old_elem, _, new_text in changes:
        new_elem = clone_with_text(old_elem, new_text)
        doc.text.insertBefore(new_elem, old_elem)
        doc.text.removeChild(old_elem)

    if changes:
        save_doc(doc, args.file)
    emit({"success": True, "replacements": len(changes)})


# ── argument parser ───────────────────────────────────────────────────────────

EXAMPLES = """
examples:
  uv run scripts/odt.py file-info report.odt
  uv run scripts/odt.py read-text report.odt --limit 20
  uv run scripts/odt.py get-paragraph report.odt --index 3
  uv run scripts/odt.py set-paragraph report.odt --index 3 --text "Updated text"
  uv run scripts/odt.py append-paragraph report.odt --text "New paragraph"
  uv run scripts/odt.py append-paragraph report.odt --text "Chapter 2" --style h2
  uv run scripts/odt.py insert-paragraph report.odt --index 2 --text "Inserted text"
  uv run scripts/odt.py delete-paragraph report.odt --index 5 --confirm
  uv run scripts/odt.py list-headings report.odt
  uv run scripts/odt.py find-replace report.odt --find "old text" --replace "new text"
  uv run scripts/odt.py create doc.odt --title "My Document"
"""

_STYLE_HELP = (
    "Block style: default, h1–h6 (headings), title, subtitle. "
    "Any other value is passed as a named paragraph style (default: default)."
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="odt.py",
        description="Read and write ODT (OpenDocument Text) files.",
        epilog=EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version="odt.py 1.0")
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    # create
    p = sub.add_parser(
        "create",
        help="Create a new ODT file.",
        description="Create a new empty ODT file.",
        epilog="Output: {success, path[, title]}",
    )
    p.add_argument("file", help="Path for the new .odt file.")
    p.add_argument("--title", metavar="TITLE", help="Set the document title in metadata.")
    p.add_argument("--overwrite", action="store_true",
                   help="Overwrite if the file already exists.")
    p.set_defaults(func=cmd_create)

    # file-info
    p = sub.add_parser(
        "file-info",
        help="Show document metadata.",
        description="Show metadata: title, paragraph/heading counts, word count.",
        epilog="Output: {path, title, paragraphs, headings, total_blocks, words}",
    )
    p.add_argument("file", help="Path to the .odt file.")
    p.set_defaults(func=cmd_file_info)

    # read-text
    p = sub.add_parser(
        "read-text",
        help="Read document content as blocks.",
        description=(
            "Read paragraphs and headings as a JSON array. "
            "Each block has an index, type (paragraph or heading), and text. "
            "Use --limit and --offset to paginate large documents."
        ),
        epilog="Output: {total, offset, returned, blocks: [{index, type, text[, level, style]}, ...]}",
    )
    p.add_argument("file", help="Path to the .odt file.")
    p.add_argument("--offset", type=int, default=0, metavar="N",
                   help="Skip the first N blocks (default: 0).")
    p.add_argument("--limit", type=int, metavar="N",
                   help="Return at most N blocks. Omit to return all.")
    p.set_defaults(func=cmd_read_text)

    # get-paragraph
    p = sub.add_parser(
        "get-paragraph",
        help="Get a single block by index.",
        description="Get a single paragraph or heading by its 0-based index.",
        epilog="Output: {index, type, text[, level, style]}",
    )
    p.add_argument("file", help="Path to the .odt file.")
    p.add_argument("--index", type=int, required=True, metavar="N",
                   help="0-based block index.")
    p.set_defaults(func=cmd_get_paragraph)

    # set-paragraph
    p = sub.add_parser(
        "set-paragraph",
        help="Replace text of a block.",
        description=(
            "Replace the text of a block at the given index. "
            "Preserves the block's type and style unless --style is given. "
            "Warning: loses inline formatting (bold, italic, etc.)."
        ),
        epilog="Output: {success, index, text}",
    )
    p.add_argument("file", help="Path to the .odt file.")
    p.add_argument("--index", type=int, required=True, metavar="N",
                   help="0-based block index.")
    p.add_argument("--text", required=True, help="New text for the block.")
    p.add_argument("--style", metavar="STYLE", help=_STYLE_HELP)
    p.set_defaults(func=cmd_set_paragraph)

    # append-paragraph
    p = sub.add_parser(
        "append-paragraph",
        help="Append a block at the end.",
        description="Append a new paragraph or heading at the end of the document.",
        epilog="Output: {success, index, text}",
    )
    p.add_argument("file", help="Path to the .odt file.")
    p.add_argument("--text", required=True, help="Text for the new block.")
    p.add_argument("--style", default="default", metavar="STYLE", help=_STYLE_HELP)
    p.set_defaults(func=cmd_append_paragraph)

    # insert-paragraph
    p = sub.add_parser(
        "insert-paragraph",
        help="Insert a block at a given position.",
        description=(
            "Insert a new paragraph or heading before the block at the given index. "
            "If index is beyond the last block, appends at the end."
        ),
        epilog="Output: {success, index, text}",
    )
    p.add_argument("file", help="Path to the .odt file.")
    p.add_argument("--index", type=int, required=True, metavar="N",
                   help="0-based index to insert before.")
    p.add_argument("--text", required=True, help="Text for the new block.")
    p.add_argument("--style", default="default", metavar="STYLE", help=_STYLE_HELP)
    p.set_defaults(func=cmd_insert_paragraph)

    # delete-paragraph
    p = sub.add_parser(
        "delete-paragraph",
        help="Delete a block (requires --confirm).",
        description="Permanently delete a paragraph or heading by index. Requires --confirm.",
        epilog="Output: {success, deleted_index, deleted_text}",
    )
    p.add_argument("file", help="Path to the .odt file.")
    p.add_argument("--index", type=int, required=True, metavar="N",
                   help="0-based block index.")
    p.add_argument("--confirm", action="store_true",
                   help="Required. Confirms you intend to permanently delete this block.")
    p.set_defaults(func=cmd_delete_paragraph)

    # list-headings
    p = sub.add_parser(
        "list-headings",
        help="List all headings.",
        description="List all heading blocks with their level, index, and text.",
        epilog="Output: {headings: [{index, level, text}, ...], count: N}",
    )
    p.add_argument("file", help="Path to the .odt file.")
    p.set_defaults(func=cmd_list_headings)

    # find-replace
    p = sub.add_parser(
        "find-replace",
        help="Find and replace text.",
        description=(
            "Find and replace all occurrences of a string across all blocks. "
            "Use --dry-run to preview changes without saving. "
            "Warning: loses inline formatting on modified blocks."
        ),
        epilog="Output: {success, replacements} or {dry_run, matches, changes: [...]}",
    )
    p.add_argument("file", help="Path to the .odt file.")
    p.add_argument("--find", required=True, metavar="TEXT", help="Text to search for.")
    p.add_argument("--replace", required=True, metavar="TEXT", help="Replacement text.")
    p.add_argument("--dry-run", action="store_true", dest="dry_run",
                   help="Preview changes without modifying the file.")
    p.set_defaults(func=cmd_find_replace)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
