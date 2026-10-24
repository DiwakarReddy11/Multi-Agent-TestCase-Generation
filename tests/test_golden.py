"""The golden data is code too: a typo in a label would silently corrupt every evaluation."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from testgen.evaluation.golden import GoldenDataset, golden_files, load_golden
from testgen.ingestion.parsers import parse_document

GOLDEN_FILES = golden_files()


def test_at_least_one_golden_dataset_exists() -> None:
    assert GOLDEN_FILES, "no evals/datasets/*/golden.yaml found"


@pytest.fixture(params=GOLDEN_FILES, ids=lambda p: p.parent.name)
def dataset(request: pytest.FixtureRequest) -> GoldenDataset:
    path: Path = request.param
    return load_golden(path)


def test_srs_file_exists_and_parses(dataset: GoldenDataset) -> None:
    assert parse_document(dataset.srs_path).blocks


def test_every_section_label_exists_in_the_srs(dataset: GoldenDataset) -> None:
    sections = {block.section for block in parse_document(dataset.srs_path).blocks}
    labelled = {r.source.section for r in dataset.requirements if r.source}
    labelled |= {s for case in dataset.retrieval for s in case.relevant_sections}
    assert labelled <= sections, f"unknown sections: {labelled - sections}"


def test_every_original_id_appears_in_the_srs(dataset: GoldenDataset) -> None:
    text = parse_document(dataset.srs_path).text
    missing = [r.original_id for r in dataset.requirements if r.original_id not in text]
    assert not missing


def test_requirement_ids_are_numbered_in_order(dataset: GoldenDataset) -> None:
    ids = [r.id for r in dataset.requirements]
    assert ids == [f"REQ-{n:03d}" for n in range(1, len(ids) + 1)]


def test_duplicate_requirement_ids_are_rejected() -> None:
    requirement = {
        "id": "REQ-001",
        "title": "Login",
        "description": "Users can log in with email and password.",
        "type": "functional",
        "obligations": [{"type": "positive", "description": "Valid credentials log the user in"}],
    }
    with pytest.raises(ValidationError, match="duplicate requirement ids"):
        GoldenDataset.model_validate(
            {"name": "x", "srs_file": "x.md", "requirements": [requirement, requirement]}
        )
