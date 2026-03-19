# AGENTS.md

This file provides guidance to agents when working with code in this repository.

TradeResearch is an AI-assisted trading-research platform and private workspace. The repo is currently early-stage, so the operating system for delivery is defined by documentation first.

Core working rules:

- No development without an issue. Every code change must map to a GitHub issue such as a story, bug, chore, or epic follow-up.
- No coding on `main`. Create a feature branch before implementation. Preferred pattern: `feat/<issue>-<slug>`, `fix/<issue>-<slug>`, `chore/<issue>-<slug>`.
- Default to TDD. Start with a failing test or a reproducible failing check, then implement the smallest passing change.
- Keep strong quality gates: unit tests for logic, integration tests for boundaries, e2e tests for critical workflows, and green CI before merge.
- Use a guarded phase model: Intake -> Plan -> Implement -> Verify -> Document -> Review -> Merge.
- Preserve context explicitly. Every issue should leave behind durable documentation so future agents do not need deep context reconstruction.

Documentation memory system:

- Use [docs/01-development-operating-system.md](/Users/thomasfey-grytnes/Projekte/Trading%20App/docs/01-development-operating-system.md) for delivery policy.
- Use [docs/02-agent-memory-and-mcp-strategy.md](/Users/thomasfey-grytnes/Projekte/Trading%20App/docs/02-agent-memory-and-mcp-strategy.md) for Roo, MCP, graph, and memory strategy.
- Use [docs/templates/change-record-template.md](/Users/thomasfey-grytnes/Projekte/Trading%20App/docs/templates/change-record-template.md) for issue-level implementation records.
- Store issue implementation records under `docs/changes/`.
- Record durable architecture decisions under `docs/architecture/` once the codebase grows.

Roo and MCP guidance:

- Use `.roo/rules/` for workspace-wide instructions and `.roo/rules-{mode}/` for mode-specific instructions.
- Use Roo memory MCP for durable facts, decisions, and glossary-level knowledge that should survive across tasks.
- Use Codeix as the preferred graph/code-index MCP for structural navigation once configured for this repo.
- Keep MCP usage disciplined: retrieve targeted context, then convert important findings into repo docs rather than relying on repeated rediscovery.
- Preferred Roo workflows are available through project slash commands:
  - `/start-issue`
  - `/refresh-context`
  - `/close-issue`
  - `/record-learning`
