# Development Operating System

## Goal

Define a delivery system that keeps TradeResearch high-signal, testable, reproducible, and easy for future AI agents to navigate without expensive context reconstruction.

## Core Policy

- No development without a GitHub issue.
- No implementation on `main`.
- Every implementation branch must point to one issue.
- Every behavior change must carry test evidence.
- Every completed issue must leave a durable change record.

## Standard Flow

1. Create or refine an issue.
2. Define acceptance criteria.
3. Create a feature branch.
4. Write the first failing test or reproducible failing check.
5. Implement the smallest passing change.
6. Run verification checks.
7. Update docs and the issue change record.
8. Open a pull request.
9. Merge only after green CI and checklist completion.

## Branching

Recommended branch names:

- `feat/<issue>-<slug>`
- `fix/<issue>-<slug>`
- `chore/<issue>-<slug>`
- `docs/<issue>-<slug>`

Examples:

- `feat/23-idea-intake-model`
- `fix/87-episode-overlap-bug`

## Issue Discipline

Recommended issue types:

- story
- bug
- chore
- spike
- epic

Each issue should define:

- problem or opportunity
- acceptance criteria
- out-of-scope items
- expected tests
- documentation impact

## Testing Policy

Default to TDD when writing or changing code.

Expected test layers:

- Unit tests: pure logic, transforms, business rules, state derivation.
- Integration tests: database boundaries, file/artifact flows, service composition, MCP adapters if added in code.
- E2E tests: critical user or operator flows through the management interface and core research pipeline.

For this project specifically, also prefer:

- deterministic fixtures for market-data preparation
- regression tests for state computation and target generation
- snapshot or golden tests for critical derived artifacts where useful

## Definition of Done

An issue is not done until all of the following are true:

- implementation is linked to an issue
- work happened on a feature branch
- tests cover the changed behavior at the right level
- relevant checks are green
- docs were updated
- a change record exists in `docs/changes/`
- the PR summary explains the change and residual risks

## Recommended GitHub Setup

### Issues

Use issue forms in `.github/ISSUE_TEMPLATE/` for:

- story
- bug
- chore
- spike

Disable blank issues to keep intake structured.

### Pull Requests

Use a PR template that requires:

- linked issue
- summary of change
- test evidence
- doc updates
- risk and rollback notes

### Rulesets

As of March 15, 2026, GitHub Docs indicate repository rulesets are available for public repositories on GitHub Free, which fits this repository.

Recommended `main` ruleset:

- require pull request before merging
- require status checks to pass
- require branch to be up to date before merging
- require linear history
- block force pushes
- block branch deletion

Recommended required checks:

- `lint`
- `typecheck`
- `unit`
- `integration`
- `e2e-smoke`
- `docs-guard`

### Merge Queue

Do not design around merge queue for this repository.

As of March 15, 2026, GitHub Docs indicate merge queue is available for public repositories owned by organizations, not for user-owned public repositories like `tgrytnes/TradeResearch`.

### Environments and Deployment Gates

Use GitHub Actions for CI/CD. Keep the pipeline phase-based:

1. Static checks
2. Unit tests
3. Integration tests
4. E2E smoke tests
5. Build/package
6. Deploy preview or staging
7. Promote only from green, reviewed artifacts

If GitHub environment protection features are insufficient for the chosen plan, implement equivalent gates in the workflow itself with explicit promotion jobs and manual approvals where needed.

## Documentation Policy

The repository itself must explain:

- what exists
- where it lives
- how it works
- how it is tested
- how to debug it

That means every substantial issue should leave behind:

- a change record in `docs/changes/`
- a feature doc if user-visible or workflow-visible behavior changed
- a runbook if failure analysis or operational procedure changed
- an architecture note if boundaries or core design changed

## Suggested Next Repo Files

- `.github/ISSUE_TEMPLATE/story.yml`
- `.github/ISSUE_TEMPLATE/bug.yml`
- `.github/ISSUE_TEMPLATE/chore.yml`
- `.github/ISSUE_TEMPLATE/config.yml`
- `.github/pull_request_template.md`
- `.github/workflows/ci.yml`
- `.github/workflows/cd.yml`

## Research Basis

- Roo Code custom instructions, modes, and MCP docs
- GitHub Docs for issue forms, PR templates, rulesets, and merge queue availability
