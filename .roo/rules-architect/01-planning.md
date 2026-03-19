# Architect Mode Planning

- Turn rough work into issue-shaped plans with acceptance criteria, test strategy, and documentation impact.
- Require an explicit path from issue -> branch -> implementation -> verification -> documentation -> merge.
- For architecture changes, produce a durable document or ADR before large implementation begins.
- Define the test plan up front:
  - unit scope
  - integration scope
  - e2e scope
  - fixtures, datasets, or replay artifacts needed
- Prefer designs that reduce future context-search cost by making module ownership, boundaries, and operational behavior explicit in docs.
- When MCP tools are available, use graph/index and memory capabilities to improve planning, then persist conclusions in repo documents.
