# TradeResearch

TradeResearch is a personal workbench for market research, trading idea validation, and private project management.

The first specialized use case is short-horizon research on DAX futures using tick-level data and derived market-state representations. The platform is intended to help capture ideas, formalize hypotheses, test variants, document findings, review visual evidence, and promote only robust concepts toward strategy design.

The system is intentionally method-agnostic. It should support:
- rule-based research
- statistical testing
- ML models
- transformer-based sequence models
- graph-based market representations
- LLM-assisted research workflows

## Core goals

- Create a structured research workflow for trading ideas
- Build a reusable private workspace/project-management foundation
- Keep market representation explicit and versioned
- Separate research logic from management/UI concerns
- Preserve research memory through findings, notes, and artifacts
- Support both human interpretation and AI-assisted research

## Initial architecture direction

- ClickHouse as the canonical raw futures tick and quote store
- PostgreSQL as the future application and workflow metadata store
- Python modules as the research engine
- Streamlit as a lightweight management and review UI
- Parquet files plus artifact storage for interchange, archives, graphs, and evidence files

## Documentation

- `AGENTS.md`
- `docs/README.md`
- `docs/01-development-operating-system.md`
- `docs/02-agent-memory-and-mcp-strategy.md`
- `docs/architecture/adr-001-storage-and-source-of-truth.md`
- `docs/runbooks/clickhouse-local-setup.md`
- `docs/runbooks/continuous-futures-rollover.md`
- `docs/templates/change-record-template.md`
- `docs/changes/README.md`
