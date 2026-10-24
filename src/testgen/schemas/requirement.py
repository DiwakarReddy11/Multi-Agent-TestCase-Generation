"""Requirement: one atomic, testable statement extracted from an SRS."""

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

# Canonical IDs are assigned by our code, so every agent can rely on one format.
RequirementId = Annotated[str, Field(pattern=r"^REQ-\d{3,}$", examples=["REQ-001"])]


class RequirementType(StrEnum):
    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"


class Priority(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SourceRef(BaseModel):
    """Where in the SRS a requirement came from, so every test traces back to a page."""

    document: str
    section: str | None = None
    page: int | None = Field(default=None, ge=1)


class Requirement(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    id: RequirementId
    original_id: str | None = Field(
        default=None, description="The ID used in the SRS itself, e.g. 'FR-3.2'"
    )
    title: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=10)
    type: RequirementType
    priority: Priority = Priority.MEDIUM
    acceptance_criteria: list[str] = Field(default_factory=list)
    source: SourceRef | None = None
