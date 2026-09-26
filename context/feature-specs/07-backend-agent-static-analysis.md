# Unit 07 — `backend_agent` Static Analysis

## Goal

Implement ephemeral repo cloning, Tree-sitter/Semgrep PII-logging
detection, and Gemini-generated remediation patches (FR-3.1 – FR-3.5),
with guaranteed cleanup on every exit path (Invariant 2).

## Design

Feeds the "Terminal & AST Agent Logs" panel with `[backend_agent]`
lines matching the exact narration style in the master-prompts doc
(e.g. "Scanning user_controller.py...", "Found plain-text PII log on
Line 14...").

## Implementation

1. Set `apps/api/agents/prompts/backend_agent.md` to the exact system
   prompt from `master-prompts-and-ui-ux-v3.md` §2.4, verbatim.
2. Clone the target repo into a tmpfs path inside a `try/finally`
   that calls `shutil.rmtree` on every exit, including exceptions
   (Invariant 2) — this is not optional and is covered by its own
   test, not just a code-review note.
3. Write `.semgrepignore` excluding `node_modules/`, `vendor/`,
   `.git/`, static assets, per FR-3.2; target only route handlers,
   ORM models, and logger statements to keep memory `<2GB`.
4. Add the PII-logging Semgrep rule from
   `agent-flow-and-interagent-bus-v3.md` §4.2
   (`dpdp-plaintext-pii-logging`) to
   `apps/api/tools/semgrep-rules/`, plus equivalents for JS/TS, Go,
   and Java loggers (FR-3.1 requires all four languages).
5. FR-3.3: inspect DB schema/ORM models for field-level encryption
   markers and required `created_at`/`updated_at`/`deleted_at`
   timestamps.
6. FR-3.4: inspect cron/scheduled-task definitions and DB triggers
   for automated purge-on-consent-withdrawal logic.
7. FR-3.5: for each Semgrep hit, feed the flagged function context to
   Gemini 3.5 Flash and generate a Unified Diff patch that fixes only
   the flagged issue (mask/hash the PII, do not otherwise alter the
   function); write it to `code_patches` with `status =
   'PENDING_REVIEW'`.
8. Every `audit_findings` row this agent writes carries the DPDP
   Section it violates (e.g. Section 8(5) for PII logging, Section
   8(7)/8(8) for retention/erasure) per Invariant 3.

## Dependencies

- `tree-sitter` + language grammars, `semgrep` CLI/library, Vertex AI
  Gemini 3.5 Flash client, a git-clone utility with shallow-clone
  support to limit tmpfs usage.

## Verification Checklist

- [ ] After a scan completes (success or failure), the tmpfs clone
      directory no longer exists on disk — verified by an explicit
      test, including a forced-exception case
- [ ] A repo with a known plaintext-PII log line is correctly flagged
      with `act_section = 'Section 8(5)'`
- [ ] The generated `.patch` applies cleanly and changes only the
      flagged lines
- [ ] Container memory during a scan stays under 2GB on a
      representative repo
- [ ] `code_patches.status` is `PENDING_REVIEW` for every
      newly-generated patch — nothing is auto-applied
