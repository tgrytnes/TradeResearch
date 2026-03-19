# Core Workflow & Memory

- **Phase Model:** Plan -> Implement (TDD) -> Verify -> Document.
- **Issues & Branches:** Never code on `main`. Always create a feature branch (`feat/`, `fix/`, `chore/`) tied to an issue.
- **Testing:** Default to TDD. Start with a failing test when practical.
- **MCP Usage:** Use `codeix-traderesearch` (for graph/code index) and `memory-traderesearch` (for cross-task facts) when helpful to gain context, but do not overuse them for trivial tasks.
- **Durable Memory:** Minimize deep context rediscovery. If you discover an important architecture or workflow fact, document it in `docs/` rather than relying solely on the memory MCP.
- **Change Records:** Always create or update the change record in `docs/changes/<issue>-<slug>.md` before closing an issue.
