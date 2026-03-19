# 50 Research Platform Architecture

## Issue

- GitHub issue: [#50](https://github.com/tgrytnes/TradeResearch/issues/50)
- Branch: `docs/50-research-platform-architecture`
- Status: in progress

## Goal

Create the first durable architecture note for TradeResearch so future implementation work has a stable reference for system boundaries, core entities, source-of-truth rules, lifecycle flow, and cross-epic relationships.

## Scope

- In scope:
  - create [docs/architecture/01-research-platform-architecture.md](../architecture/01-research-platform-architecture.md)
  - link the new architecture note from [docs/README.md](../README.md)
  - summarize the intent and verification in a change record
- Out of scope:
  - final database schema
  - API contract design
  - detailed UI wireframes
  - deployment implementation

## Implementation Summary

- Added a new umbrella architecture note covering system context, subsystem boundaries, core domain entities, lifecycle flow, source-of-truth rules, traceability expectations, and epic-to-architecture mapping.
- Chose a durable, foundation-first structure so the document can guide multiple future stories without being rewritten for every implementation detail.
- Key files involved:
  - [docs/architecture/01-research-platform-architecture.md](../architecture/01-research-platform-architecture.md)
  - [docs/README.md](../README.md)
  - [docs/changes/50-research-platform-architecture.md](./50-research-platform-architecture.md)

## Tests

- Unit: not applicable for documentation-only change
- Integration: not applicable for documentation-only change
- E2E: not applicable for documentation-only change
- Manual verification:
  - reviewed alignment with Epics [#1](https://github.com/tgrytnes/TradeResearch/issues/1) through [#12](https://github.com/tgrytnes/TradeResearch/issues/12)
  - reviewed alignment with stories [#13](https://github.com/tgrytnes/TradeResearch/issues/13) through [#49](https://github.com/tgrytnes/TradeResearch/issues/49) where they shape architecture boundaries
  - verified internal repository links in the new docs content

## Debugging Notes

- Symptoms observed:
  - the repository had process and workflow documentation but no durable architecture note under [docs/architecture/](../architecture/)
- Root cause:
  - architectural intent existed in epics and supporting docs but had not yet been consolidated into a dedicated architecture reference
- Failure modes to watch:
  - later implementation may drift if ADR-level decisions are not captured when detailed choices are made
  - the umbrella note may become too broad if story-level specifics are added instead of split into follow-on notes

## Documentation Updated

- Docs changed:
  - [docs/README.md](../README.md)
  - [docs/changes/50-research-platform-architecture.md](./50-research-platform-architecture.md)
- Runbooks changed:
  - none
- Architecture notes changed:
  - [docs/architecture/01-research-platform-architecture.md](../architecture/01-research-platform-architecture.md)

## Follow-ups

- Remaining risks:
  - detailed storage, lifecycle specialization, and provenance decisions still need ADR-level treatment
- Deferred work:
  - create follow-on ADR notes once implementation stories begin
- New issues to open:
  - ADR issue for storage and source-of-truth boundaries
  - ADR issue for entity and lifecycle specialization
  - ADR issue for representation versioning and run provenance
