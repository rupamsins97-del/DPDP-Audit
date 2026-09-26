# Progress Tracker — DPDP 360° AI Compliance Auditor

Update this file after every meaningful implementation change.

## Current Phase

- Complete: All 17 Units Built, Deployed, and Verified

## Current Goal

- All 17 Units Completed & Production Deployed (`context/feature-specs/00-build-plan.md`)

## Completed

- Unit 01 — `context/feature-specs/01-repo-and-env-scaffold.md` (Monorepo skeleton, Next.js 15, FastAPI, tooling configs, design tokens, .env.example)
- Unit 02 — `context/feature-specs/02-supabase-schema-and-rls.md` (Full schema migration 0001_init.sql, pgvector HNSW, pg_cron 365-day retention, multi-tenant RLS, auth bootstrap trigger)
- Unit 03 — `context/feature-specs/03-auth-and-org-isolation.md` (Supabase Auth SSR/client integration, FastAPI JWT verification dependency, organization scoping, isolation test suite)
- Unit 04 — `context/feature-specs/04-fastapi-gateway-shell.md` (Pydantic schemas, POST /audits, GET /audits/{id}, GET /audits/{id}/stream SSE endpoint stub, response envelope)
- Unit 05 — `context/feature-specs/05-langgraph-orchestrator-skeleton.md` (LangGraph multi-agent StateGraph DAG, in-memory async EventBus, GOVERNANCE_RULES_READY broadcasting, FastAPI BackgroundTasks execution runner, state reducers, and verification test suite)
- Unit 06 — `context/feature-specs/06-policy-agent-rag-pipeline.md` (Statutory corpus chunking & pgvector ingestion script, policy_agent master prompt, transient in-memory PDF parsing, legal claims extraction FR-1.1–FR-1.3, pgvector cosine similarity grounding FR-1.4, and GOVERNANCE_RULES_READY event bus dispatch)
- Unit 07 — `context/feature-specs/07-backend-agent-static-analysis.md` (Ephemeral repo cloning with guaranteed cleanup on all exit paths, multi-language Semgrep/AST PII-logging detection rules for Python/TS/Go/Java, DB model encryption/timestamp check, purge-on-withdrawal trigger check, Gemini Unified Diff patch generation, and PENDING_REVIEW patches)
- Unit 08 — `context/feature-specs/08-frontend-agent-browser-automation.md` (Stagehand/Playwright browser automation, CDP pre-consent tracker interception, AXTree consent-UI extraction & unbundled verification, withdrawal-parity step analysis, Scrapfly anti-bot proxy routing, and statutory citations)
- Unit 09 — `context/feature-specs/09-domain-extension-agents.md` (Domain extension agents: incident_management_agent, child_safety_agent, dpr_portal_agent, 72h DPB breach pipeline, DigiLocker VPC, <=90d DPR timers, and statutory citations)
- Unit 10 — `context/feature-specs/10-synthesis-agent-and-scoring.md` (Lead synthesis agent reconciliation, statutory misrepresentation cross-referencing Sec 6(1), DPDP Compliance Index domain-weighted formula, zero-tolerance critical cap <=59%, SHA-256 state hash for tamper-evidence NFR-3, and Invariant 3 statutory grounding validation)
- Unit 11 — `context/feature-specs/11-ui-shell-input-configuration.md` (Layout Pattern 1 single centered card on dark theme, shadcn UI components, client-side URL & Git validation, drag-and-drop PDF validator with inline error handling, framework selector, and zero-network local state submission)
- Unit 12 — `context/feature-specs/12-ui-shell-telemetry-stream.md` (Layout Pattern 2 dual-pane full-viewport telemetry stream: Live Browser Execution and Terminal & AST Agent Logs, isolated useTelemetryStream hook, intelligent auto-scroll with pause-on-scroll-up and jump-to-latest resume, and agent color tagging)
- Unit 13 — `context/feature-specs/13-ui-shell-reconciliation-dashboard.md` (Layout Pattern 3 Reconciliation Dashboard: Overall DPDP Compliance Index gauge/badge with PASS/WARN/FAIL bands, 6-domain weighted score cards, tamper-evident SHA-256 state hash display, findings table with exact Violation Title / Severity / Section / Action columns, and modal action preview)
- Unit 14 — `context/feature-specs/14-wire-audit-submission-and-telemetry.md` (Wired Next.js frontend to FastAPI backend: real POST /audits submission with session auth and error banner, real-time EventSource SSE telemetry stream with query-token auth, EventBus multi-agent log subscription, resilient reconnecting state without log buffer loss, and automated dashboard navigation on COMPLETED)
- Unit 15 — `context/feature-specs/15-wire-dashboard-to-live-findings.md` (Wired Reconciliation Dashboard to real GET /audits/{id} endpoint: live compliance score and band rendering, dynamic 6-domain statutory calculations, mapped agent actions, organization isolation error boundaries, dedicated zero-findings 100% compliant state banner, and report export JSON download)
- Unit 16 — `context/feature-specs/16-remediation-patch-review-flow.md` (Interactive remediation diff viewer modal, GET /findings/{id}/patch and POST /patches/{id}/approve|reject endpoints, real-time status overrides without full reload, direct DPA clause and SQL retention script file downloads, and Invariant 4 masked PII traces)
- Unit 17 — `context/feature-specs/17-deployment-mcp-pipeline.md` (Antigravity-driven MCP deployment pipeline: Google Cloud Run backend deployed in `asia-south1` [https://dpdp-auditor-api-3ryg6y5r3q-el.a.run.app], live smoke-test audit submission & SSE stream verified, Next.js frontend production bundle compiled with live Cloud Run API integration, and SR-1 statutory data residency confirmed in `asia-south1`)

## In Progress

- None (All 17 Units 100% complete and verified)

## Next Up

- Production Maintenance & Scaling


## Open Questions

- None currently open. All 6 core architectural questions resolved and incorporated into context files.

## Architecture Decisions

- **Six-File Context System & Build Plan (2026-09-19)**: Authored from v3 planning docs. Decomposed into a 17-unit dependency-ordered build plan; see `context/feature-specs/00-build-plan.md`.
- **Git PR Scope Decision (Unit 16)**: Approving a patch updates `code_patches.status` to `APPLIED` and commits the remediation metadata in PostgreSQL. Direct automated GitHub PR creation is modularized and triggered when repository credentials/GitHub App tokens are configured in the organization settings, while retaining manual export/download for air-gapped repositories.
- **Monorepo Layout**: `apps/web` (Next.js 15), `apps/api` (FastAPI + LangGraph agents), `supabase/` (migrations) — chosen so the FastAPI gateway stays the single point of Supabase service-role access.
- **Auth & Multi-Tenant Model (Resolved)**: Supabase Auth (`auth.users`) with `organizations` and `organization_members` tables. PostgreSQL trigger on user creation auto-bootstraps organization and assigns user as `ADMIN`. RLS enforces membership subquery `organization_id IN (SELECT organization_id FROM organization_members WHERE user_id = auth.uid())`.
- **Legal PDF Ephemeral Handling (Resolved)**: Uploaded Privacy Policy and DPA PDFs are processed transiently in-memory into `legal_embeddings` vector chunks; raw binary PDF files are discarded immediately and never persisted to blob storage (consistent with Invariant 2 & Invariant 4).
- **Telemetry Streaming Protocol (Resolved)**: Server-Sent Events (SSE) exclusively via `GET /audits/{id}/telemetry` over HTTP/2 with structured, agent-tagged event frames.
- **Vertex AI Model Garden Identifiers (Resolved)**: Configured via `.env` with regional support in `asia-south1`:
  - Agentic / AST reasoning: `gemini-1.5-flash-002` / `gemini-2.0-flash` (`VERTEX_AI_GEMINI_FLASH_MODEL`)
  - Deep legal reasoning: `gemini-1.5-pro-002` (`VERTEX_AI_GEMINI_PRO_MODEL`)
  - Embeddings: `text-embedding-004` (768-dim) (`VERTEX_AI_EMBEDDING_MODEL`)
- **Compliance Index Composite Formula (Resolved)**: Domain-weighted scoring:
  - Frontend Consent & Tracking: 25%
  - Backend PII Security & Plaintext Logging: 25%
  - Legal Governance & DPA Alignment: 20%
  - Children's Data Protection: 10%
  - Incident Management & 72h SLA: 10%
  - DPR & Grievance Redressal: 10%
  - *Zero-Tolerance Critical Cap*: If any `CRITICAL` statutory misrepresentation or pre-consent tracker finding is present, the final Compliance Index is hard-capped at 59% (FAIL).
- **Event Bus Pub/Sub vs Redis Architecture (Unit 05)**: Built an asynchronous, in-memory pub/sub EventBus (`apps/api/tools/event_bus.py`) wrapping Python `asyncio.Queue` per-subscriber channels for single-instance Cloud Run containers and local development. It emits typed events such as `GOVERNANCE_RULES_READY` and `TELEMETRY_LOG` without external infrastructure overhead, while maintaining an interface that supports switching to Google Cloud Pub/Sub if horizontal multi-instance orchestration is introduced.
- **Legal Semantic Chunking & Statutory Grounding (Unit 06)**: Statutory texts in `context/RAG/` are split on section/rule boundaries with hierarchical context prefixing and embedded into 768-dim vectors (`text-embedding-004`). Every governance finding emitted by `policy_agent` or downstream worker agents is grounded against this knowledge base, guaranteeing non-null `act_section` and `rules_clause` citations (Invariant 3). Uploaded legal PDFs are processed transiently in-memory with `pypdf` with zero persistence to disk or blob storage (Invariants 2 & 4).

## Session Notes

- Source docs are versioned "v3" (system-architecture-tech-stack-v3, project-requirements-document-v3, master-prompts-and-ui-ux-v3, agent-flow-and-interagent-bus-v3).
- All 6 initial architectural ambiguities have been resolved and codified across `architecture.md`, `progress-tracker.md`, and relevant feature specs.
