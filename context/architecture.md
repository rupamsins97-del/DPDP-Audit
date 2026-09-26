# Architecture Context — DPDP 360° AI Compliance Auditor

## Stack

| Layer | Technology | Role |
| --- | --- | --- |
| Frontend UI | Next.js 15 (React 19) + Tailwind CSS | Input/config screen, real-time SSE telemetry stream, reconciliation dashboard. Deployed on Vercel/Netlify. |
| Backend Gateway | FastAPI (Python 3.12) | REST + SSE surface, request validation (Pydantic v2), auth verification, job enqueuing. Deployed on GCP Cloud Run (`asia-south1`). |
| Agent Framework | LangGraph (Python) | State-machine DAG orchestration: parallel worker dispatch, state persistence, inter-agent event bus. |
| LLM — agentic/AST | Vertex AI `gemini-1.5-flash-002` / `gemini-2.0-flash` | Fast, structured agentic web navigation (Stagehand) and backend AST-fix/patch generation (`VERTEX_AI_GEMINI_FLASH_MODEL`). |
| LLM — legal reasoning | Vertex AI `gemini-1.5-pro-002` | Deep legal RAG reasoning over DPDP Act 2023, DPDP Rules 2025, and DPAs (`VERTEX_AI_GEMINI_PRO_MODEL`). |
| Embeddings | Vertex AI `text-embedding-004` | 768-dim vectors for legal statutory chunk indexing (`VERTEX_AI_EMBEDDING_MODEL`). |
| Browser agent engine | Stagehand (on Playwright/CDP) + Scrapfly Unblocker | AI-driven web navigation, AXTree trimming, network interception, anti-bot bypass. |
| Static analysis | Semgrep + Tree-sitter | AST construction, taint tracking, deterministic SAST, `<2GB` memory via `.semgrepignore`. |
| Database & vector store | Supabase PostgreSQL 16 + `pgvector` | Relational (`audits`, `audit_findings`, `code_patches`, `organizations`, `organization_members`) + vector store (`legal_embeddings`), RLS, `pg_cron` 365-day retention. Hosted `asia-south1`. |
| Event bus | GCloud Pub/Sub or Redis | Inter-agent async events (`GOVERNANCE_RULES_READY`, etc.) and telemetry dispatch. |
| Telemetry Stream | Server-Sent Events (SSE) | Unidirectional event stream (`GET /audits/{id}/telemetry`) over HTTP/2 with typed event frames. |
| Build-time IDE | Google Antigravity + MCPs | Supabase MCP (migrations), Cloud Run MCP (backend deploy), Vercel/Netlify MCP (frontend deploy). |

## System Boundaries

- `apps/web/` — Next.js frontend. Owns UI rendering, the SSE client, and dashboard state. Never calls Supabase directly with elevated privileges; all data access goes through `apps/api/`.
- `apps/api/` — FastAPI gateway. Owns the HTTP/SSE surface, request validation, auth/session verification, and job enqueuing. Contains no agent reasoning of its own.
- `apps/api/agents/` — LangGraph graph definition plus one module per agent (`synthesis_agent`, `policy_agent`, `frontend_agent`, `backend_agent`, `incident_management_agent`, `child_safety_agent`, `dpr_portal_agent`). Owns all LLM prompting and tool orchestration.
- `apps/api/agents/prompts/` — the master system prompt for each agent, one file per agent, versioned independently of the code that calls it.
- `apps/api/tools/` — deterministic tool wrappers agents call: Stagehand/CDP driver, Semgrep/Tree-sitter runner, Vertex AI embedding client, Pub/Sub or Redis event-bus client.
- `apps/api/tools/semgrep-rules/` — versioned `.yml` Semgrep detection rules.
- `supabase/migrations/` — SQL migrations, RLS policies, `pg_cron` jobs, `legal_embeddings` seed scripts. Append-only once applied.
- `context/` — this Six-File Context System.

## Storage Model

- **Database (Supabase Postgres in `asia-south1`)**:
  - `organizations`: Tenant metadata (`id`, `name`, `created_at`).
  - `organization_members`: User-organization mapping (`organization_id`, `user_id`, `role`, `created_at`).
  - `audits`: Run metadata, status, compliance score, state hash.
  - `audit_findings`: Per-finding evidence, cited Act Section / Rules Clause, severity, masked snippet.
  - `code_patches`: Generated Unified Diffs, review status (`PENDING_REVIEW`, `APPLIED`, `REJECTED`).
  - `legal_embeddings`: DPDP Act/Rules chunks and transiently uploaded document chunks + 768-dim vectors for RAG.
- **Ephemeral compute only (never persisted)**:
  - Cloned source-code repositories: ephemeral tmpfs only, deleted via `shutil.rmtree` immediately after AST parsing (Invariant 2).
  - Uploaded Privacy Policy / DPA PDFs: processed transiently in-memory into `legal_embeddings` text chunks and discarded immediately; raw binary PDF files are never stored in blob storage or persistent disk (Invariant 2 / Invariant 4).
  - Live browser/CDP session state and in-flight LangGraph scratch state.

## Auth and Access Model

- **Authentication Provider**: Supabase Auth (`auth.users`).
- **Organization Multi-Tenancy**: Every user belongs to an organization via `organization_members`. An automatic database trigger on `auth.users` bootstraps a default organization for new signups and sets the user as `ADMIN`.
- **Request Authorization**: Requests to `apps/api/` carry a Bearer JWT. The FastAPI gateway verifies the token and resolves the authenticated user's `organization_id`.
- **Row Level Security (RLS)**: Enforced on all audit tables using the membership subquery:
  ```sql
  organization_id IN (
    SELECT organization_id FROM organization_members
    WHERE user_id = auth.uid()
  )
  ```
- **Service-Role Boundary**: Only the backend gateway uses the Supabase service-role key; the frontend only holds session-scoped anon-key tokens.

## Invariants

1. API request handlers never run long-lived agent work synchronously. `POST /audits` enqueues a LangGraph run and returns immediately; all agent execution is observed via SSE (`GET /audits/{id}/telemetry`), not by blocking the request.
2. Cloned source-code repositories and uploaded legal PDFs exist only in ephemeral tmpfs/memory and are purged immediately after AST parsing / vector chunking. They are never written to Supabase blob storage or any path that survives the request.
3. Every row written to `audit_findings` cites an explicit DPDP Act Section or Rule number. An agent may not emit a finding it cannot ground in a specific statutory clause (NFR-1).
4. Any PII appearing in an evidence snippet is hashed (SHA-256) or masked before it is written to Supabase. Raw PII is never persisted (SR-3).
5. All GCP and Supabase resources are provisioned in `asia-south1` or `asia-south2` only (SR-1 / Section 16).
6. RLS policies enforce organization-level isolation on every audit-related table. Once a policy is applied via migration, it is changed only by a new migration — never rewritten in place.
7. `audits` and related execution logs are retained for exactly 365 days via `pg_cron` and then purged automatically (SR-4). No manual retention overrides.
8. The DPDP Compliance Index formula uses domain-weighted deduction (Frontend 25%, Backend 25%, Governance 20%, Children 10%, Incident 10%, DPR 10%) with an automatic hard cap of 59% (FAIL) if any `CRITICAL` statutory misrepresentation or pre-consent tracking finding exists.
