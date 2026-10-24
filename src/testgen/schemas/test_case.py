"""TestCase: one executable test, always linked to at least one requirement."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from testgen.schemas.requirement import Priority, RequirementId

# Phrases that sound like an expected result but can't be checked by a tester.
VAGUE_PHRASES = ("as expected", "works correctly", "works fine", "should work", "behaves correctly")


class TestType(StrEnum):
    __test__ = False  # stop pytest from treating this as a test class

    POSITIVE = "positive"
    NEGATIVE = "negative"
    BOUNDARY = "boundary"
    EDGE = "edge"


class TestStep(BaseModel):
    __test__ = False

    action: str = Field(min_length=3)
    expected: str | None = None


class TestCase(BaseModel):
    __test__ = False
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    id: str = Field(pattern=r"^TC-\d{3,}$", examples=["TC-001"])
    requirement_ids: list[RequirementId] = Field(min_length=1)
    title: str = Field(min_length=5, max_length=150)
    type: TestType
    priority: Priority = Priority.MEDIUM
    preconditions: list[str] = Field(default_factory=list)
    steps: list[TestStep] = Field(min_length=1, max_length=15)
    test_data: dict[str, str] = Field(default_factory=dict)
    expected_result: str = Field(min_length=10)

    @field_validator("expected_result")
    @classmethod
    def expected_result_must_be_concrete(cls, value: str) -> str:
        if any(phrase in value.lower() for phrase in VAGUE_PHRASES):
            raise ValueError(f"too vague: {value!r}. Describe an observable outcome.")
        return value
