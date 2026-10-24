from typing import Any

import pytest
from pydantic import ValidationError

from testgen.schemas import Requirement, TestCase, TestType


def valid_requirement(**overrides: Any) -> dict[str, Any]:
    data = {
        "id": "REQ-001",
        "title": "Account lockout",
        "description": "The system shall lock an account after 5 failed login attempts.",
        "type": "functional",
        "priority": "high",
    }
    return data | overrides


def valid_test_case(**overrides: Any) -> dict[str, Any]:
    data = {
        "id": "TC-001",
        "requirement_ids": ["REQ-001"],
        "title": "Lock account after 5 wrong passwords",
        "type": "negative",
        "steps": [{"action": "Enter a wrong password 5 times"}],
        "expected_result": "Account is locked and the message 'Account locked' is shown",
    }
    return data | overrides


def test_valid_requirement_round_trips_through_json() -> None:
    req = Requirement.model_validate(valid_requirement())
    assert Requirement.model_validate_json(req.model_dump_json()) == req


def test_whitespace_is_stripped() -> None:
    req = Requirement.model_validate(valid_requirement(title="  Account lockout  "))
    assert req.title == "Account lockout"


@pytest.mark.parametrize("bad_id", ["REQ-1", "req-001", "FR-001", "REQ001"])
def test_requirement_id_format_is_enforced(bad_id: str) -> None:
    with pytest.raises(ValidationError):
        Requirement.model_validate(valid_requirement(id=bad_id))


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        Requirement.model_validate(valid_requirement(confidence=0.9))


def test_valid_test_case_parses_enums() -> None:
    tc = TestCase.model_validate(valid_test_case())
    assert tc.type is TestType.NEGATIVE


def test_test_case_must_trace_to_a_requirement() -> None:
    with pytest.raises(ValidationError):
        TestCase.model_validate(valid_test_case(requirement_ids=[]))


def test_test_case_rejects_malformed_requirement_ids() -> None:
    with pytest.raises(ValidationError):
        TestCase.model_validate(valid_test_case(requirement_ids=["login-feature"]))


@pytest.mark.parametrize("vague", ["Login works as expected", "The page works correctly"])
def test_vague_expected_results_are_rejected(vague: str) -> None:
    with pytest.raises(ValidationError, match="too vague"):
        TestCase.model_validate(valid_test_case(expected_result=vague))


def test_json_schema_carries_field_descriptions_for_the_llm() -> None:
    schema = Requirement.model_json_schema()
    assert "FR-3.2" in schema["properties"]["original_id"]["description"]
