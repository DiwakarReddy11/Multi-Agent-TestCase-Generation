import pytest
from pydantic import ValidationError

from testgen.config import Settings
from testgen.llm import build_chat_model


def test_env_vars_override_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GENERATOR_MODEL", "groq:some-model")
    monkeypatch.setenv("LLM_TIMEOUT_S", "15")
    s = Settings(_env_file=None)
    assert s.generator_model == "groq:some-model"
    assert s.llm_timeout_s == 15  # text "15" was converted to the int 15


def test_invalid_number_fails_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_TIMEOUT_S", "abc")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_api_keys_are_hidden_when_printed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "gsk_super_secret")
    s = Settings(_env_file=None)
    assert "gsk_super_secret" not in repr(s)


def test_unknown_provider_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported provider"):
        build_chat_model("nonexistent:model", Settings(_env_file=None))


def test_openrouter_spec_keeps_free_suffix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    model = build_chat_model("openrouter:vendor/model:free", Settings(_env_file=None))
    assert model.model_name == "vendor/model:free"
