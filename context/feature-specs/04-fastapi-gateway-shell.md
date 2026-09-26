# Unit 04 — FastAPI Gateway Shell

## Goal

Stand up the FastAPI surface — health check, `AuditContextState`
Pydantic schemas, `POST /audits` (persists a row, does not run any
agent yet), and an SSE endpoint stub — so Unit 05 has a real HTTP
layer to plug the orchestrator into.

## Design

No UI. Backend-only, consumed later by Unit 14's wiring pass.

## Implementation

1. Define Pydantic models mirroring the `AuditContextState` JSON
   schema in `agent-flow-and-interagent-bus-v3.md` exactly
   (`audit_id`, `organization_id`, `status`, `governance_promises`,
   `findings` per agent role, `generated_patches`).
2. `GET /health` — trivial liveness check, no auth required.
3. `POST /audits` — validated by the auth dependency from Unit 03;
   accepts `target_url`, optional `repo_url`, uploaded legal docs
   (stored as an upload reference, not parsed here), and framework
   selection; writes a row to `audits` with `status = 'IN_PROGRESS'`;
   returns `audit_id` immediately (Invariant 1 — no agent run is
   awaited here).
4. `GET /audits/{audit_id}/stream` — SSE endpoint stub that, for now,
   emits only a `status` event reflecting the `audits.status` column;
   real per-agent event streaming arrives in Unit 05/14.
5. `GET /audits/{audit_id}` — returns the current `AuditContextState`
   snapshot (status + any findings so far) for the dashboard's later
   use in Unit 15.
6. Response envelope and error handling per `code-standards.md`.

## Dependencies

- `fastapi`, `pydantic>=2`, `sse-starlette` (or equivalent) for the
  SSE endpoint, `python-multipart` for file upload handling.

## Verification Checklist

- [ ] `POST /audits` returns an `audit_id` in well under a second
      with no agent logic executed
- [ ] The new `audits` row is scoped to the caller's
      `organization_id` and invisible to a different org's session
      (re-verify Unit 03's isolation against this new route)
- [ ] `GET /audits/{audit_id}/stream` opens an SSE connection and
      emits at least the current status
- [ ] Every route rejects malformed input at the Pydantic layer with
      a structured error, before any DB call
- [ ] Uploaded legal-doc files are stored as a reference only (no
      parsing logic in this unit) and are not written into
      `legal_embeddings` yet — that's Unit 06's job
