# UI Context — DPDP 360° AI Compliance Auditor

## Theme

Dark technical workspace — this is a security/compliance tool read
by legal and engineering reviewers, not a consumer product. Near-
black backgrounds, layered surfaces for the dual-pane telemetry
stream, and severity-coded accent colors that must read clearly at a
glance in a findings table. No light mode in v1.

## Colors

All components use these CSS custom-property tokens — no hardcoded
hex values.

| Role | CSS Variable | Value |
| --- | --- | --- |
| Page background | `--bg-base` | `#0a0b0d` |
| Surface (cards, panels) | `--bg-surface` | `#14161a` |
| Raised surface (modals) | `--bg-raised` | `#1c1f24` |
| Primary text | `--text-primary` | `#e6e8eb` |
| Muted text | `--text-muted` | `#8b909a` |
| Primary accent | `--accent-primary` | `#3b82f6` |
| Border | `--border-default` | `#2a2d33` |
| Severity — Critical | `--severity-critical` | `#ef4444` |
| Severity — High | `--severity-high` | `#f97316` |
| Severity — Medium | `--severity-medium` | `#eab308` |
| Severity — Low | `--severity-low` | `#64748b` |
| Compliance — Pass (≥90%) | `--state-success` | `#22c55e` |
| Compliance — Warn (60–89%) | `--state-warn` | `#eab308` |
| Compliance — Fail (<60%) | `--state-error` | `#ef4444` |

## Typography

| Role | Font | Variable |
| --- | --- | --- |
| UI text | Geist Sans | `--font-sans` |
| Code / terminal logs / AST snippets | Geist Mono | `--font-mono` |

## Border Radius

| Context | Class |
| --- | --- |
| Inline / small UI (badges, pills) | `rounded-md` |
| Cards / panels | `rounded-lg` |
| Modals / overlays | `rounded-xl` |

## Component Library

shadcn/ui on top of Tailwind. Components live in `apps/web/components/ui/`.
Use the CLI to add new primitives rather than writing them from
scratch; the findings table is a styled shadcn `Table`, not a custom
grid.

## Layout Patterns — the three-screen journey

1. **Input & Configuration** — single centered card: target URL,
   optional repo URL, legal-doc upload (drag/drop), framework
   selector (DPDP Act 2023 / Rules 2025), and a prominent
   "Start 360° Audit" primary-accent button. No results visible yet.
2. **Real-Time Telemetry Stream** — full-viewport split into two
   panels side by side: left = "Live Browser Execution" (Stagehand/
   CDP narration), right = "Terminal & AST Agent Logs" (backend_agent
   scan output, patch generation). Both panels auto-scroll and are
   fed by the same SSE connection, tagged by agent name.
3. **Reconciliation Dashboard** — top: a Compliance Index gauge/badge
   (colored via the Compliance tokens above) with a WARN/PASS/FAIL
   label. Below: a findings table — columns exactly `Violation Title
   | Severity | Section | Action` — where Action renders one of
   "View Network Trace", "Apply Auto-Fix PR", "Generate DB Script",
   "Download DPA Clause" depending on the finding's `agent_role`.

- Sidebars: none in v1 — this is a linear three-step flow, not a
  persistent-nav app.
- Modals: centered overlay with backdrop blur, used for patch-review
  (diff viewer) and network-trace detail.

## Icons

Lucide React. Stroke-based icons only. `h-4 w-4` for inline (table
action icons, severity badges), `h-5 w-5` for buttons.
