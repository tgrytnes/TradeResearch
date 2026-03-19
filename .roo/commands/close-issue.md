---
description: Close an issue, run checks, and update docs
argument-hint: <issue-number> <slug>
mode: code
---

Close out GitHub issue $ARGUMENTS.

1. Verify relevant checks pass (lint, typecheck, tests).
2. Create or update the change record in `docs/changes/`.
3. Update relevant project docs (architecture, features) if applicable.
4. (Optional) Store a short summary in `memory-traderesearch` if a durable lesson was learned.
5. Provide a concise PR-ready summary.
