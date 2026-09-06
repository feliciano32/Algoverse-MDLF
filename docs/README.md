# docs

| file | what it is |
|---|---|
| `REVIEW_RESPONSE_MAP.md` | reviewer feedback triaged, with where each item lands in the paper |
| `PROPOSED_EDITS.md` | the annotated edit list against the original draft |

## Still to add

These live in the project notes and should be copied in — they are the running record of
what was found and what changed:

- **`FINDINGS.md`** — the findings log. F0 (the coordinate-space bug that invalidated the
  first grid) through F16, plus the positive results P1–P6. Marks retracted conclusions
  rather than deleting them, so nobody acts on superseded advice.
- **`REVIEWER_CHECKLIST.md`** — every reviewer item with its current status and the
  evidence that closes it.
- **`TEAM_SPLIT.md`** — task allocation with inputs, outputs, and which reviewer item each
  task closes.
- **`RERUN_PLAN.md`** — what had to be regenerated after F0, and why.

## Why the findings log is worth versioning

Two conclusions in this project were stated confidently and later retracted: a left/right
detection asymmetry with an anatomical explanation, and a size effect at p = 0.031. Both
were artefacts of the coordinate bug. A log that records the retraction alongside the
original claim is the only reliable defence against re-deriving a dead result six weeks
later, which happened here more than once.
