"""Command-line interface. Run `uv run testgen --help`."""

import argparse
import logging
import sys
from pathlib import Path

from testgen.ingestion.parsers import UnsupportedDocumentError
from testgen.ingestion.pipeline import ingest_file
from testgen.ingestion.vector_store import get_chunk_store
from testgen.retrieval.retriever import DEFAULT_MIN_SCORE, retrieve


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="testgen", description="Generate test cases from SRS documents."
    )
    commands = parser.add_subparsers(dest="command", required=True)

    ingest = commands.add_parser("ingest", help="parse, chunk, embed and store an SRS file")
    ingest.add_argument("path", type=Path)

    search = commands.add_parser("search", help="find SRS text related to a question")
    search.add_argument("query")
    search.add_argument("--document", help="only search this document (its file name)")
    search.add_argument("-k", type=int, default=5, help="maximum number of results")
    search.add_argument(
        "--min-score", type=float, default=DEFAULT_MIN_SCORE, help="hide weaker matches"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    # Our own INFO logs, but only warnings from noisy libraries.
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    logging.getLogger("testgen").setLevel(logging.INFO)

    store = get_chunk_store()
    if args.command == "ingest":
        try:
            report = ingest_file(args.path, store)
        except (FileNotFoundError, UnsupportedDocumentError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(f"Ingested {report.document}: {report.blocks} blocks -> {report.chunks} chunks")
        return 0

    results = retrieve(
        store, args.query, document=args.document, k=args.k, min_score=args.min_score
    )
    if not results:
        print("No relevant text found.")
    for result in results:
        chunk = result.chunk
        preview = chunk.text.replace("\n", " ")[:90]
        page = chunk.page or "-"
        print(f"{result.score:.2f}  {chunk.document} | page {page} | {chunk.section}")
        print(f"      {preview}")
    return 0
