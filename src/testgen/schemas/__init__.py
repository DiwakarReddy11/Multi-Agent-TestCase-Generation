"""Data contracts shared by every agent."""

from testgen.schemas.document import Chunk, ParsedDocument, RetrievedChunk, TextBlock
from testgen.schemas.requirement import (
    Priority,
    Requirement,
    RequirementId,
    RequirementType,
    SourceRef,
)
from testgen.schemas.test_case import TestCase, TestStep, TestType

__all__ = [
    "Chunk",
    "ParsedDocument",
    "Priority",
    "Requirement",
    "RequirementId",
    "RequirementType",
    "RetrievedChunk",
    "SourceRef",
    "TestCase",
    "TestStep",
    "TestType",
    "TextBlock",
]
