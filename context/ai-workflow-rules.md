# AI Workflow Rules — DPDP 360° AI Compliance Auditor

## Approach

Build this project incrementally using a spec-driven workflow. The
context files define what to build, how to build it, and the current
state of progress. Always implement against these specs — do not
infer or invent agent behavior, DPDP statutory citations, or UI
copy from scratch. If a detail is genuinely undecided, it belongs in
"Open Questions" in `progress-tracker.md`, not in your judgment call.

## Scoping Rules

- Work on exactly one unit from `context/feature-specs/00-build-plan.md`
  at a time, in the numbered order given.
- Prefer small, verifiable increments — a unit that touches both a
  Supabase migration and an agent's LLM prompt is a signal to split.
- Do not combine unrelated system boundaries (see `architecture.md`)
  in a single implementation step — e.g. never combine an
  `apps/api/agents/` change with an `apps/web/` change in the same
  unit unless the unit's spec explicitly says so (the "wiring" units
  are the deliberate exception).

## When to Split Work

Split an implementation step if it combines:

- A Supabase migration/RLS change and application logic that depends
  on it
- Two different agents' reasoning logic
- Backend agent logic and its corresponding frontend wiring
- Any behavior not clearly defined in a feature-spec file

If a change cannot be verified end to end quickly, the scope is too
broad — split it.

## Handling Missing Requirements

- Do not invent DPDP Act/Rule citations, agent prompts, compliance
  scoring formulas, or UI text not defined in the context files or
  the v3 planning documents.
- If a requirement is ambiguous (e.g. exact Compliance Index
  weighting across agents, exact PDF-retention behavior, exact auth
  provider), resolve it in the relevant context file *before*
  implementing — do not silently pick one and move on.
- If a requirement is missing outright, add it as an open question in
  `progress-tracker.md` and wait for Rupam's sign-off before building
  against an assumption.

## Protected Files

Do not modify the following unless explicitly instructed:

- `supabase/migrations/*.sql` that have already been applied to a
  live database — RLS policies are never rewritten in place; ship a
  new migration instead.
- `apps/api/agents/prompts/*.md` — the master system prompt for each
  agent is legally load-bearing (NFR-1 zero-hallucination grounding).
  Changing one is a deliberate, reviewed decision, not a refactor.
- `apps/api/tools/semgrep-rules/*.yml` — SAST rule changes affect
  every past and future audit's findings; treat as a reviewed change.
- `components/ui/*` — generated shadcn/ui library components.

## Non-negotiables

- No invented, renumbered, or skipped feature-spec files.
- RLS is never rewritten in place, only extended via new migrations.
- Cloned source code is never persisted — every backend_agent code
  path that clones a repo must guarantee cleanup on all exit paths.
- No raw PII is ever written to Supabase, in any table, for any
  reason, even temporarily.
- Agent system prompts live in dedicated files, never inline strings.

## Keeping Docs in Sync

Update the relevant context file whenever implementation changes:

- System architecture or boundaries → `architecture.md`
- Storage model decisions → `architecture.md`
- Code conventions or standards → `code-standards.md`
- Feature scope → `project-overview.md`

## Before Moving to the Next Unit

1. The current unit works end to end within its defined scope
2. No invariant defined in `architecture.md` was violated
3. `progress-tracker.md` reflects the completed work
4. `npm run build` (frontend) and the backend's test/lint command
   both pass
