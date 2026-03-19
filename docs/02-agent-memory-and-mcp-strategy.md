# Agent Memory and MCP Strategy

## Goal

Use Roo Code's current instruction and MCP capabilities to reduce repeated context-search cost and make TradeResearch easy for AI assistants to understand and extend.

## Roo Capabilities Relevant to This Repo

Roo currently supports:

- `AGENTS.md` in the workspace root
- `AGENTS.local.md` for personal local overrides
- workspace rules in `.roo/rules/`
- mode-specific rules in `.roo/rules-{modeSlug}/`
- project-specific modes in `.roomodes`
- project-level MCP config in `.roo/mcp.json`
- MCP tool execution through `use_mcp_tool`
- MCP resource retrieval through `access_mcp_resource`

These capabilities make it possible to separate:

- high-level repository policy
- mode-specific behavior
- persistent memory
- graph/index-assisted structural navigation

## Local Roo State Discovered on This Machine

Current global Roo setup already includes:

- `memory`
- `roo-filesystem`
- several `codeix-*` MCP servers for other repositories

This repository now has a project-local MCP bootstrap design:

- `memory-traderesearch` for project-specific durable memory
- `codeix-traderesearch` for project-specific graph and index navigation

Repository-local docs and workflow commands are also in place so Roo has explicit guidance on when to use them.

## Why This Matters

Chat history is expensive and fragile. A strong agent workflow should not depend on rediscovering the same facts every session.

The repository should carry the durable memory for:

- workflow rules
- architectural decisions
- feature boundaries
- debugging entry points
- implementation history

MCP should augment this, not replace it.

## Recommended MCP Roles

### 1. Memory MCP

Use the memory server for cross-task, durable working knowledge such as:

- glossary
- open questions
- active design tensions
- repeated implementation traps
- stable facts discovered across multiple tasks

Do not use memory as the only source of truth for important project knowledge. If a fact is important for future implementation, promote it into repo docs.

### 2. Codeix Graph MCP

Codeix is currently available locally via `npx codeix` and supports:

- `build` to create a `.codeindex/`
- `serve` to run an MCP server
- graph/index-based repository exploration

Recommended use:

- symbol discovery
- impact analysis before refactors
- locating relevant code paths quickly
- understanding relationships across modules

Project-level MCP setup:

- `.roo/mcp.json.example` is the portable template
- `.roo/mcp.json` is the local machine-specific config for this repository

### 3. Roo Filesystem MCP

Use the filesystem MCP sparingly for:

- reading shared memory-bank artifacts
- browsing curated external context that should remain outside the repo

Do not let important implementation knowledge live only in external files if it belongs in the repo.

## Recommended Agent Workflow with MCP

1. Read repo guidance first: `AGENTS.md` and `.roo/rules-*`.
2. Use Codeix to locate the relevant code graph when implementation work begins.
3. Use Memory MCP to recall prior decisions, unresolved questions, and known pitfalls.
4. Convert stable conclusions into repo docs:
   - `docs/changes/`
   - `docs/architecture/`
   - `docs/runbooks/`
   - `docs/features/`

This keeps MCP for acceleration while the repository remains the durable source of truth.

## Repository Workflows Added

Project slash commands now exist for:

- `.roo/commands/start-issue.md`
- `.roo/commands/refresh-context.md`
- `.roo/commands/close-issue.md`
- `.roo/commands/record-learning.md`

These commands are designed to make Roo:

- recover context from docs first
- use Codeix for structure when needed
- use project memory for prior decisions and pitfalls
- update repository docs and durable memory at the end of work

## Proposed Documentation Memory Model

### AGENTS Layer

Purpose:

- fast, high-signal repository rules
- workflow constraints
- links to durable docs

Files:

- `AGENTS.md`
- `AGENTS.local.md.example`

### Roo Rules Layer

Purpose:

- richer workspace-wide and mode-specific behavior

Files:

- `.roo/rules/01-workflow.md`
- `.roo/rules/02-context-memory.md`
- `.roo/rules-code/01-code-delivery.md`
- `.roo/rules-architect/01-planning.md`
- `.roo/rules-debug/01-debugging.md`
- `.roo/rules-ask/01-research.md`

### Durable Repo Docs Layer

Purpose:

- minimize future deep search
- explain what changed and where to look

Recommended directories:

- `docs/changes/`
- `docs/architecture/`
- `docs/runbooks/`
- `docs/features/`

## Suggested Change Record Standard

For each issue, store:

- issue link
- goal
- implementation summary
- files touched
- tests added or updated
- failure modes and debugging notes
- follow-up work

Use `docs/templates/change-record-template.md`.

## Initialization and Ongoing Use

Recommended initialization:

1. keep `.roo/mcp.json` local and machine-specific
2. run `codeix build -r <repo>` once to create the initial `.codeindex/`
3. let Roo start `codeix-traderesearch` through MCP when needed
4. use `memory-traderesearch` for concise durable summaries
5. keep repository docs as the detailed source of truth

## Research Basis

- Official Roo docs for custom instructions, custom modes, MCP usage, and MCP tools
- Current local Roo config on this machine
- Official Codeix CLI help output on this machine
