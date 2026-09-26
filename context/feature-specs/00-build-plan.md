# Build Plan — DPDP 360° AI Compliance Auditor

Strict dependency order. Do not start unit N+1 until unit N is
verified complete per `ai-workflow-rules.md`. Ordering rules applied:
dependencies first, security before functionality, backend before
frontend wiring, UI shells before real data.

| # | Unit | Depends on | One-line goal |
| - | --- | --- | --- |
| 01 | Repo & environment scaffold | — | Monorepo skeleton (`apps/web`, `apps/api`, `supabase/`), `.env.example`, tooling config. |
| 02 | Supabase schema & RLS | 01 | Create `audits`, `audit_findings`, `code_patches`, `legal_embeddings`; enable `pgvector`/`pg_cron`; apply RLS + retention job. |
| 03 | Auth & org isolation | 02 | Session auth, `organization_id` scoping enforced in the gateway before any data path exists. |
| 04 | FastAPI gateway shell | 01, 03 | Health check, Pydantic schemas, `POST /audits` (persists only, no agent run yet), SSE endpoint stub. |
| 05 | LangGraph orchestrator skeleton | 04 | `AuditContextState` schema, graph wiring, `synthesis_agent` stub node, event-bus client — no real agent logic yet. |
| 06 | `policy_agent` RAG pipeline | 02, 05 | Legal doc parsing, embedding ingestion, pgvector similarity search, governance-promise extraction. |
| 07 | `backend_agent` static analysis | 05 | Ephemeral clone → Tree-sitter/Semgrep scan → purge; PII-logging detection; Gemini patch generation. |
| 08 | `frontend_agent` browser automation | 05 | Stagehand/CDP pre-consent interception, AXTree consent audit, withdrawal-parity test, Scrapfly routing. |
| 09 | Domain extension agents | 05, 06 | `incident_management_agent`, `child_safety_agent`, `dpr_portal_agent`. |
| 10 | `synthesis_agent` & scoring | 06, 07, 08, 09 | Full parallel DAG dispatch, promise-vs-reality reconciliation, Compliance Index, hashed audit trail. |
| 11 | UI shell — Input & Configuration | 01 | Static screen: URL/repo/doc inputs, framework selector, Start button. Local state only. |
| 12 | UI shell — Telemetry Stream | 01 | Static dual-pane telemetry screen with mock/looped log data. |
| 13 | UI shell — Reconciliation Dashboard | 01 | Static dashboard: compliance gauge + findings table against mock data. |
| 14 | Wire audit submission & telemetry | 04, 05, 11, 12 | Real `POST /audits` call; real SSE stream into the telemetry screen. |
| 15 | Wire dashboard to live findings | 10, 13 | Real compliance score + findings from Supabase via the gateway. |
| 16 | Remediation & patch-review flow | 07, 15 | Diff viewer modal, apply/reject endpoints against `code_patches`. |
| 17 | Deployment & MCP build pipeline | 02–16 | Antigravity-driven Supabase MCP migrations, Cloud Run MCP deploy, Vercel/Netlify MCP deploy. |

## Notes on ordering

- Units 02–03 (storage + auth) come before unit 04 (the gateway) so
  no route is ever written against an un-secured table.
- Units 06–09 (the six worker agents) come before unit 10 (synthesis)
  because synthesis has nothing to reconcile without worker output —
  and 10 is also where the parallel-dispatch DAG gets its final shape.
- Units 11–13 (UI shells) can start any time after unit 01 and run in
  parallel with backend units 02–10, since they use mock data only —
  this is the "UI shells before real data" rule in practice.
- Units 14–16 are the wiring pass: nothing in `apps/web` calls a real
  endpoint until its corresponding backend unit is verified complete.
- Unit 17 is last: it deploys what already works locally/staged, it
  does not build new functionality.
