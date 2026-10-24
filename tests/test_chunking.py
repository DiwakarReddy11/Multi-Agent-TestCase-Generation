from testgen.ingestion.chunking import chunk_document
from testgen.schemas import ParsedDocument, TextBlock

REQUIREMENT_LINES = [
    f"FR-{i}: The system shall handle scenario number {i} for library members." for i in range(30)
]


def make_doc(*blocks: TextBlock) -> ParsedDocument:
    return ParsedDocument(name="srs.pdf", blocks=list(blocks))


def test_small_blocks_become_one_chunk_each_with_their_location() -> None:
    doc = make_doc(
        TextBlock(text="Members can borrow books.", page=3, section="2.3 Borrowing"),
        TextBlock(text="Search by title.", page=4, section="2.2 Search"),
    )
    chunks = chunk_document(doc)
    assert [(c.text, c.page, c.section, c.index) for c in chunks] == [
        ("Members can borrow books.", 3, "2.3 Borrowing", 0),
        ("Search by title.", 4, "2.2 Search", 1),
    ]


def test_long_block_is_split_without_cutting_a_requirement_line() -> None:
    doc = make_doc(TextBlock(text="\n".join(REQUIREMENT_LINES), section="2 Functional"))
    chunks = chunk_document(doc, chunk_size=300, chunk_overlap=0)

    assert len(chunks) > 1
    assert all(len(c.text) <= 300 for c in chunks)
    for line in REQUIREMENT_LINES:
        assert any(line in c.text for c in chunks), f"line was cut: {line}"


def test_overlap_repeats_context_between_neighbouring_chunks() -> None:
    doc = make_doc(TextBlock(text="\n".join(REQUIREMENT_LINES)))
    first, second, *_ = chunk_document(doc, chunk_size=300, chunk_overlap=100)
    last_line_of_first = first.text.splitlines()[-1]
    assert second.text.startswith(last_line_of_first)


def test_chunk_ids_are_unique_and_stable_across_runs() -> None:
    doc = make_doc(TextBlock(text="\n".join(REQUIREMENT_LINES)))
    first_run = [c.id for c in chunk_document(doc, chunk_size=300)]
    second_run = [c.id for c in chunk_document(doc, chunk_size=300)]
    assert first_run == second_run
    assert len(set(first_run)) == len(first_run)


def test_embedding_text_includes_the_section_heading() -> None:
    block = TextBlock(text="Loans are limited to 5.", section="2.3 Borrowing")
    [chunk] = chunk_document(make_doc(block))
    assert chunk.text_for_embedding == "2.3 Borrowing\nLoans are limited to 5."
