## Application Building Context — DPDP 360° AI Compliance Auditor

Read the following files in order before implementing or making any
architectural decision. Do not skip ahead to feature specs without
having read all six core context files at least once this session.

1. `context/project-overview.md` — what the Auditor does, who it's
   for, in/out of scope, success criteria
2. `context/architecture.md` — stack, system boundaries, storage
   model, auth/access model, invariants (read this before touching
   any agent, API route, or migration)
3. `context/ui-context.md` — theme, color tokens, typography, the
   three-screen layout pattern
4. `context/code-standards.md` — Python/FastAPI/LangGraph and
   TypeScript/Next.js conventions, API route rules, data rules
5. `context/ai-workflow-rules.md` — scoping rules, protected files,
   how to handle missing/ambiguous requirements
6. `context/progress-tracker.md` — current phase, completed units,
   open questions, session notes

Then read `context/feature-specs/00-build-plan.md` for the
dependency-ordered unit sequence, and only the ONE feature-spec file
for the unit currently in progress (per `progress-tracker.md`).

## Non-negotiables (apply from session start)

- Never invent, renumber, or skip feature-spec files. If a unit
  looks wrong or missing, stop and flag it in `progress-tracker.md`
  — do not silently fill the gap.
- RLS policies, once applied via a migration, are never rewritten in
  place. Changes to access rules ship as a new migration.
- Agent system prompts live in dedicated prompt files under
  `apps/api/agents/prompts/`, never inline in Python source.
- Cloned source-code repositories are ephemeral (tmpfs) only. They
  are never written to Supabase, blob storage, or any persistent
  disk path, per Invariant 2 in `architecture.md`.
- Every compliance finding written to `audit_findings` must cite an
  explicit DPDP Act Section or Rule clause. No ungrounded findings.
- Update `context/progress-tracker.md` after each meaningful
  implementation change.

If implementation changes the architecture, scope, or standards
documented in the context files, update the relevant file before
continuing.
