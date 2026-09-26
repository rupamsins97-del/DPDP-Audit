# Unit 11 — UI Shell: Input & Configuration

## Goal

Build the static Input & Configuration screen — target URL, repo
URL, legal-doc upload, framework selector, Start button — using only
local component state. No API calls yet.

## Design

Per `ui-context.md` layout pattern 1: a single centered card on the
dark theme. Fields: `Target URL` (text input), `Repo URL` (text
input, optional), `Upload Legal Docs` (drag/drop file input, accepts
PDF), `Select Framework` (dropdown, pre-populated with "DPDP Act 2023
/ Rules 2025" as the only option in v1). Primary-accent
"Start 360° Audit" button, disabled until `Target URL` is filled.
Use shadcn `Card`, `Input`, `Select`, and a drag/drop file component.

## Implementation

1. Build the screen as a Client Component (`"use client"`) since it
   holds form state.
2. Client-side validation: `Target URL` must be a well-formed URL;
   `Repo URL` if present must look like a git URL; file input accepts
   only `.pdf` and rejects/flags anything else with an inline error
   (mirrors the server-side validation that Unit 04 will also apply —
   per `code-standards.md`, never trust client validation alone, so
   this is UX only, not the security boundary).
3. On submit, in this unit, just log the assembled payload to the
   console / hold it in local state — no network call (that's Unit
   14).
4. Use the severity/compliance color tokens from `ui-context.md`
   nowhere in this screen (they belong to the dashboard) — keep this
   screen visually neutral/accent-only.

## Dependencies

- shadcn/ui `Card`, `Input`, `Select`, `Button` components (added via
  the CLI per `code-standards.md`), a drag/drop file library or a
  hand-rolled `<input type="file">` styled to match.

## Verification Checklist

- [ ] The screen renders correctly against the dark theme tokens from
      `ui-context.md`, no hardcoded hex values
- [ ] "Start 360° Audit" is disabled until a valid Target URL is
      entered
- [ ] An invalid URL or a non-PDF upload shows an inline error and
      blocks submission
- [ ] No network request is made anywhere in this unit
- [ ] `npm run build` passes
