"""Golden datasets: hand-labelled answers that agents and retrieval are measured against."""

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from testgen.schemas import Requirement, TestType

DATASETS_DIR = Path("evals/datasets")


class TestObligation(BaseModel):
    """A condition a good test suite must check, e.g. 'borrowing a 6th book is rejected'."""

    __test__ = False
    model_config = ConfigDict(extra="forbid")

    type: TestType
    description: str = Field(min_length=10)


class GoldenRequirement(Requirement):
    obligations: list[TestObligation] = Field(min_length=1)


class RetrievalCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=5)
    # Empty means "the SRS doesn't answer this": retrieval should return nothing.
    relevant_sections: list[str] = Field(default_factory=list)


class GoldenDataset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    srs_file: str = Field(description="SRS file name, stored next to golden.yaml")
    requirements: list[GoldenRequirement] = Field(min_length=1)
    retrieval: list[RetrievalCase] = Field(default_factory=list)
    folder: Path = Field(default=Path(), exclude=True)

    @property
    def srs_path(self) -> Path:
        return self.folder / self.srs_file

    @model_validator(mode="after")
    def requirement_ids_are_unique(self) -> "GoldenDataset":
        ids = [r.id for r in self.requirements]
        duplicates = sorted({i for i in ids if ids.count(i) > 1})
        if duplicates:
            raise ValueError(f"duplicate requirement ids: {duplicates}")
        return self


def load_golden(path: Path) -> GoldenDataset:
    """Load and validate one golden.yaml file."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return GoldenDataset.model_validate({**data, "folder": path.parent})


def golden_files(datasets_dir: Path = DATASETS_DIR) -> list[Path]:
    return sorted(datasets_dir.glob("*/golden.yaml"))
