"""Call every configured model once. Run: uv run python scripts/smoke_llm.py"""

from testgen.config import get_settings
from testgen.llm import build_chat_model

s = get_settings()
for spec in (s.generator_model, s.judge_model, s.fallback_model):
    try:
        reply = build_chat_model(spec).invoke("Reply with exactly: OK")
        print(f"[PASS] {spec} -> {reply.text!r}")
    except Exception as exc:
        print(f"[FAIL] {spec} -> {type(exc).__name__}: {exc}")
