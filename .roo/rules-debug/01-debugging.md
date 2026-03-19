# Debug Mode

- Start with a reproducible failure and evidence, not intuition alone.
- Narrow the failure to one of:
  - logic defect
  - integration defect
  - environment/config defect
  - data/fixture defect
  - test defect
- Prefer a failing regression test before applying a fix.
- Capture debugging evidence in the issue change record or a runbook note:
  - symptoms
  - reproduction steps
  - root cause
  - fix
  - verification
- If the fix reveals a missing guardrail in CI, tests, or docs, propose the missing guardrail instead of stopping at the patch.
