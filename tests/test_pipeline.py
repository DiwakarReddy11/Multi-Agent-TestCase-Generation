from pathlib import Path

import pytest

from testgen.cli import main
from testgen.ingestion.pipeline import ingest_file
from testgen.ingestion.vector_store import ChunkStore
from testgen.retrieval.retriever import format_context, retrieve
from testgen.schemas import Chunk, RetrievedChunk

SRS_V1 = """# 2.1 Account Management
The system shall lock an account after 5 failed login attempts.

# 2.3 Borrowing
A member shall be able to borrow at most 5 books.
"""


def write_srs(tmp_path: Path, content: str = SRS_V1) -> Path:
    path = tmp_path / "library.md"
    path.write_text(content, encoding="utf-8")
    return path


def test_ingest_reports_what_it_stored(tmp_path: Path, store: ChunkStore) -> None:
    report = ingest_file(write_srs(tmp_path), store)
    assert (report.document, report.blocks, report.chunks) == ("library.md", 2, 2)
    assert store.count() == 2


def test_reingesting_an_edited_srs_replaces_old_chunks(tmp_path: Path, store: ChunkStore) -> None:
    ingest_file(write_srs(tmp_path), store)
    edited = SRS_V1.replace("at most 5 books", "at most 3 books")
    ingest_file(write_srs(tmp_path, edited), store)

    assert store.count() == 2
    texts = [r.chunk.text for r in store.search("borrow books", k=2)]
    assert not any("5 books" in t for t in texts)


def test_retrieve_drops_weak_matches(tmp_path: Path, store: ChunkStore) -> None:
    ingest_file(write_srs(tmp_path), store)
    results = retrieve(store, "lock account failed login", min_score=0.3)
    assert [r.chunk.section for r in results] == ["2.1 Account Management"]


def test_format_context_numbers_and_cites_each_chunk() -> None:
    results = [
        RetrievedChunk(
            chunk=Chunk(
                id="a",
                document="srs.pdf",
                index=0,
                text="Lock after 5.",
                page=4,
                section="2.1 Login",
            ),
            score=0.8,
        ),
        RetrievedChunk(
            chunk=Chunk(id="b", document="srs.md", index=1, text="HTTPS only."), score=0.6
        ),
    ]
    assert format_context(results) == (
        "[1] (srs.pdf, page 4, 2.1 Login)\nLock after 5.\n\n[2] (srs.md)\nHTTPS only."
    )


def test_cli_ingest_and_search(
    tmp_path: Path,
    store: ChunkStore,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("testgen.cli.get_chunk_store", lambda: store)

    assert main(["ingest", str(write_srs(tmp_path))]) == 0
    assert "library.md: 2 blocks -> 2 chunks" in capsys.readouterr().out

    # The fake embedder scores lower than the real model, so turn the threshold off.
    assert main(["search", "how many books can a member borrow", "--min-score", "0"]) == 0
    assert "2.3 Borrowing" in capsys.readouterr().out.splitlines()[0]


def test_cli_reports_bad_files_without_a_traceback(
    tmp_path: Path,
    store: ChunkStore,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("testgen.cli.get_chunk_store", lambda: store)
    bad = tmp_path / "srs.xlsx"
    bad.write_bytes(b"data")

    assert main(["ingest", str(bad)]) == 1
    assert "Unsupported file type" in capsys.readouterr().err
