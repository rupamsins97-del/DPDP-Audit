# Unit 16 — Remediation & Patch-Review Flow

## Goal

Turn the dashboard's placeholder action modals (Unit 13) into a real
patch-review workflow backed by `code_patches`: view a diff, approve
it, or reject it. Auto-fix patches are never applied without this
explicit human step.

## Design

"Apply Auto-Fix PR" opens a `Dialog` (per `ui-context.md` modal
pattern: centered overlay, backdrop blur) showing the Unified Diff in
a monospace, syntax-highlighted view, with Approve / Reject buttons.
"Generate DB Script" and "Download DPA Clause" trigger a direct
download of the relevant generated artifact. "View Network Trace"
opens a read-only detail modal of the `evidence_snippet` for that
finding (already masked/hashed per Invariant 4 — never render raw
PII even in this reviewer-only view).

## Implementation

1. `GET /findings/{finding_id}/patch` — returns the `code_patches`
   row for a finding, scoped by the caller's `organization_id`
   (joined through `audit_findings.audit_id -> audits.organization_id`).
2. `POST /patches/{patch_id}/approve` and
   `POST /patches/{patch_id}/reject` — update `code_patches.status`;
   approving does not push a PR automatically in v1 unless a Git
   integration is explicitly scoped — if not yet decided, log it as
   an open question in `progress-tracker.md` rather than building an
   unspecified GitHub-write integration.
3. Wire the dashboard's "Apply Auto-Fix PR" modal to these endpoints;
   render the diff with a diff-viewer component.
4. "Generate DB Script"/"Download DPA Clause" download the relevant
   text content (retention-fix SQL / extracted DPA clause) as a file,
   sourced from the finding's `remediation_suggestion` or
   `evidence_snippet` field.
5. "View Network Trace" renders `evidence_snippet` read-only, with an
   explicit UI note that PII is masked/hashed, matching Invariant 4.

## Dependencies

- A diff-viewer component (or a simple `<pre>` with monospace
  styling and +/- line coloring using the severity tokens) — no need
  for a heavyweight diff library unless review quality demands it.

## Verification Checklist

- [ ] Opening "Apply Auto-Fix PR" shows the real Unified Diff content
      for that finding
- [ ] Approve/Reject correctly update `code_patches.status` and the
      UI reflects the new status without a full page reload
- [ ] "Generate DB Script"/"Download DPA Clause" download real
      generated content, not placeholder text
- [ ] "View Network Trace" never displays unmasked PII
- [ ] Cross-organization access to another org's patch/finding is
      rejected
- [ ] The Git-push-on-approve scope decision is either implemented
      per an explicit spec or logged as an open question — not
      silently assumed
