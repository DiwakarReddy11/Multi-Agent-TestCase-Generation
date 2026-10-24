"""Turn SRS files (PDF, DOCX, Markdown, text) into blocks that remember their page and section."""

import re
from collections.abc import Callable, Iterable, Iterator
from pathlib import Path
from typing import NamedTuple

from docx import Document as open_docx
from docx.table import Table
from pypdf import PdfReader

from testgen.schemas import ParsedDocument, TextBlock

MAX_FILE_MB = 20
# Numbered headings such as "3.2 User Login" or "4.1.2. Password Rules".
NUMBERED_HEADING = re.compile(r"^\d+(\.\d+)*\.?\s+[A-Z][^.!?:]{2,80}$")
MARKDOWN_HEADING = re.compile(r"^#{1,6}\s+(.+)$")


class UnsupportedDocumentError(ValueError):
    """The file can't be turned into text: wrong type, too large, or no text layer."""


class Line(NamedTuple):
    text: str
    page: int | None
    is_heading: bool


def _looks_like_heading(text: str) -> bool:
    # "1. The system shall ..." is a numbered requirement, not a heading.
    return bool(NUMBERED_HEADING.match(text)) and " shall " not in text.lower()


def _pdf_lines(path: Path) -> Iterator[Line]:
    for page_no, page in enumerate(PdfReader(path).pages, start=1):
        for raw in (page.extract_text() or "").splitlines():
            text = raw.strip()
            yield Line(text, page_no, _looks_like_heading(text))


def _docx_lines(path: Path) -> Iterator[Line]:
    # iter_inner_content keeps paragraphs and tables in document order;
    # SRS documents often list requirements in tables.
    for item in open_docx(str(path)).iter_inner_content():
        if isinstance(item, Table):
            for row in item.rows:
                yield Line(" | ".join(cell.text.strip() for cell in row.cells), None, False)
        else:
            style = item.style.name if item.style is not None else ""
            yield Line(item.text, None, style.startswith("Heading") or style == "Title")


def _markdown_lines(path: Path) -> Iterator[Line]:
    for raw in path.read_text(encoding="utf-8").splitlines():
        match = MARKDOWN_HEADING.match(raw.strip())
        yield Line(match.group(1) if match else raw, None, match is not None)


def _text_lines(path: Path) -> Iterator[Line]:
    for raw in path.read_text(encoding="utf-8").splitlines():
        text = raw.strip()
        yield Line(text, None, _looks_like_heading(text))


PARSERS: dict[str, Callable[[Path], Iterator[Line]]] = {
    ".pdf": _pdf_lines,
    ".docx": _docx_lines,
    ".md": _markdown_lines,
    ".txt": _text_lines,
}


def _to_blocks(lines: Iterable[Line]) -> list[TextBlock]:
    """Group consecutive lines that share a page and section into one block."""
    blocks: list[TextBlock] = []
    buffer: list[str] = []
    page: int | None = None
    section: str | None = None

    def flush() -> None:
        if buffer:
            blocks.append(TextBlock(text="\n".join(buffer), page=page, section=section))
            buffer.clear()

    for line in lines:
        text = line.text.strip()
        if not text:
            continue
        if line.is_heading or line.page != page:
            flush()
            page = line.page
        if line.is_heading:
            section = text
        else:
            buffer.append(text)
    flush()
    return blocks


def parse_document(path: Path) -> ParsedDocument:
    if not path.is_file():
        raise FileNotFoundError(path)
    size_mb = path.stat().st_size / 1_000_000
    if size_mb > MAX_FILE_MB:
        raise UnsupportedDocumentError(
            f"{path.name} is {size_mb:.1f} MB; limit is {MAX_FILE_MB} MB"
        )
    parser = PARSERS.get(path.suffix.lower())
    if parser is None:
        raise UnsupportedDocumentError(
            f"Unsupported file type '{path.suffix}'. Supported: {', '.join(PARSERS)}"
        )
    blocks = _to_blocks(parser(path))
    if not blocks:
        raise UnsupportedDocumentError(
            f"No text found in {path.name}. Scanned (image-only) PDFs are not supported."
        )
    return ParsedDocument(name=path.name, blocks=blocks)
