---
description: Recover project context for a feature area using docs, memory, and Codeix
argument-hint: <topic-or-issue>
mode: ask
---

Refresh context for $ARGUMENTS.

Required workflow:

1. Read `AGENTS.md`.
2. Read the most relevant docs under `docs/`.
3. If available, query `memory-traderesearch` for durable facts, prior decisions, open questions, and known pitfalls related to this topic.
4. If available, use `codeix-traderesearch` to locate the most relevant modules, symbols, or directories.
5. Summarize:
   - what already exists
   - where the relevant code likely lives
   - where the relevant docs live
   - what the next engineer should inspect first
   - what is still unknown

Keep the answer concise and operational.
