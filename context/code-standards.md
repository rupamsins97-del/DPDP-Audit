# Code Standards — DPDP 360° AI Compliance Auditor

## General

- Keep every agent module single-purpose: one file per agent, one
  responsibility per tool wrapper. No agent calls another agent's
  LLM directly — only via the event bus or LangGraph edges.
- Fix root causes in detection rules; do not special-case around a
  bad Semgrep rule or a flaky Stagehand selector in application code.
- Do not mix legal-reasoning prompts with orchestration/control-flow
  code. Prompts live in `apps/api/agents/prompts/`.

## Python (FastAPI / LangGraph / Agents)

- Python 3.12, fully type-hinted; Pydantic v2 models for every
  request, response, and `AuditContextState` shape.
- No bare `except:`; catch specific exceptions and log with the
  `audit_id` for traceability.
- Every function that touches a cloned repository must run inside a
  `try/finally` that guarantees `shutil.rmtree` on the tmpfs path,
  even on failure (Invariant 2).
- Every function that writes to `audit_findings` must accept a
  `statute_reference` argument and reject/refuse to write a finding
  without one (Invariant 3).
- Semgrep rules live in versioned `.yml` files under
  `apps/api/tools/semgrep-rules/`, not inline strings in Python.

## TypeScript / Next.js 15

- Strict mode required throughout `apps/web/`.
- Default to Server Components; add `"use client"` only where the
  telemetry stream or dashboard needs browser-side state (SSE
  subscription, table interactivity).
- No `any` — use the shared types generated from the FastAPI Pydantic
  schemas (or hand-written mirrors, kept in one `apps/web/lib/types/`
  location) for `AuditContextState`, findings, and patches.
- Validate any user-entered URL/repo string client-side before
  submit, and again server-side in `apps/api` — never trust the
  client validation alone.

## Styling

- Tailwind CSS only; use the CSS custom-property tokens defined in
  `ui-context.md` — no hardcoded hex values in components.
- Severity colors (`CRITICAL`/`HIGH`/`MEDIUM`/`LOW`) always come from
  the token map in `ui-context.md`, never inlined per-component.

## API Routes (FastAPI)

- Validate and parse all request input with Pydantic before any
  logic runs; reject with a structured error on schema failure.
- Enforce `organization_id` scoping and auth on every route before
  any read or mutation — no route trusts a client-supplied
  `organization_id` without cross-checking the authenticated session.
- Return a consistent response envelope: `{ data, error }` on REST
  endpoints; well-formed `event:`/`data:` frames on SSE endpoints.
- `POST /audits` and any other job-enqueuing route returns
  immediately (Invariant 1) — it does not await the LangGraph run.

## Data and Storage

- Metadata, findings, patches, and embeddings belong in Supabase
  Postgres — nowhere else.
- Cloned source code, uploaded legal PDFs, and live browser session
  state never touch Supabase blob storage or any persistent disk
  (Invariant 2).
- PII in evidence is hashed or masked before it is written, at the
  point of writing — never store raw PII "temporarily" with a
  cleanup job planned for later (Invariant 4 / SR-3).

## File Organization

- `apps/web/` — Next.js frontend (input/config screen, telemetry
  stream, reconciliation dashboard)
- `apps/api/` — FastAPI gateway (routes, auth, Pydantic schemas)
- `apps/api/agents/` — LangGraph graph + one module per agent
- `apps/api/agents/prompts/` — one master system-prompt file per
  agent
- `apps/api/tools/` — Stagehand/CDP, Semgrep/Tree-sitter, Vertex AI
  embedding client, event-bus client
- `supabase/migrations/` — SQL migrations, RLS policies, `pg_cron`
  jobs
- `context/` — the Six-File Context System
