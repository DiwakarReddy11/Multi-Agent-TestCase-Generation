# Golden datasets

Hand-labelled answers for real SRS documents. Every agent, prompt and retrieval change is
scored against these files, so a wrong label means a wrong score. Treat them like code:
review every change, and keep `uv run pytest` green (`tests/test_golden.py` checks them).

## Layout

```
evals/datasets/<name>/
├── <name>_srs.md     # the SRS document (PDF, DOCX, MD or TXT)
└── golden.yaml       # the labels
```

## Labelling rules

### Requirements

1. **One testable behaviour per requirement.** Split sentences that contain two behaviours.
   "Reset via an emailed link; the link expires after 30 minutes" becomes two requirements.
   A condition on the same behaviour ("unless reserved") stays in one requirement.
2. **IDs** are `REQ-001`, `REQ-002`, … in document order. Put the SRS's own label in
   `original_id`; split requirements share the same `original_id`.
3. **`description`** restates the SRS in one clear sentence. Keep every number and limit;
   add nothing the SRS doesn't say.
4. **`type`** is `functional` (what the system does) or `non_functional` (how well:
   performance, security, availability, usability).
5. **`source.section`** is the heading exactly as the parser reports it
   (`uv run python scripts/inspect_document.py <file>`).
6. Leave `priority` out unless the SRS states it.

### Obligations (what a good test suite must check)

- Each one is a **concrete, observable condition**, written so a tester could check it:
  "A member holding 5 books cannot borrow a 6th", not "borrowing limit works".
- **`boundary`**: every number or limit gets its edge values (exactly at the limit and just past it).
- **`negative`**: every rule that rejects or blocks something gets an obligation that it does.
- **`positive`**: the normal, successful path.
- **`edge`**: unusual but valid situations (queues of two, returning on the due date, resets).
- Label only what the SRS supports. If an obligation needs an assumption, write the
  assumption into the SRS question list for the client instead.

### Retrieval cases

- Natural questions a tester or agent would ask, **worded differently from the SRS**
  (otherwise keyword matching alone would pass).
- `relevant_sections` lists every section that answers the question.
- Include questions the SRS does **not** answer, with `relevant_sections: []`; retrieval
  should return nothing for them.

## Review process

1. Label by hand, or draft with an LLM and then check every line against the SRS.
   Never draft with the generator model you are evaluating; it would grade its own style.
2. A second person (or a second pass a day later) reviews the labels.
3. Run `uv run pytest tests/test_golden.py` before committing.
