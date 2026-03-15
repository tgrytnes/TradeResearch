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

- SQL database as the system of record
- Python modules as the research engine
- Streamlit as a lightweight management and review UI
- Artifact storage for graphs and evidence files

## Documentation

- `docs/01-product-vision.md`
- `docs/02-architecture-overview.md`
- `docs/03-domain-model.md`
- `docs/04-market-representation-strategy.md`
- `docs/05-v1-scope.md`
- `docs/06-epic-alignment.md`# TradeResearch
