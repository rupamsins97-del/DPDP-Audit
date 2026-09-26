# Unit 12 — UI Shell: Telemetry Stream

## Goal

Build the static Real-Time Telemetry Stream screen — the dual-pane
"Live Browser Execution" / "Terminal & AST Agent Logs" layout — fed
by looped mock log lines, no real SSE connection yet.

## Design

Per `ui-context.md` layout pattern 2: full-viewport split into two
equal panels, both dark surfaces (`--bg-surface`) with monospace text
(`--font-mono`), auto-scrolling to the newest line. Left panel title
"Live Browser Execution", right panel title "Terminal & AST Agent
Logs" — matching the mock in `master-prompts-and-ui-ux-v3.md`.

## Implementation

1. Client Component with a small in-memory array of mock log lines
   (reuse the exact sample lines from the master-prompts mock, e.g.
   "Intercepting network...", "[backend_agent] Scanning
   user_controller.py...") appended on an interval to simulate
   streaming, purely for visual verification in this unit.
2. Each log line is tagged with its source agent (styled distinctly,
   e.g. a small colored dot or label per agent) so Unit 14 can later
   just swap the mock interval for a real SSE `onmessage` handler
   without restructuring the component.
3. Auto-scroll each panel to the bottom on new content, but stop
   auto-scrolling if the user has manually scrolled up (standard
   log-viewer UX).

## Dependencies

- No new libraries beyond what Unit 01 scaffolded.

## Verification Checklist

- [ ] Both panels render side by side at full viewport height and are
      independently scrollable
- [ ] Mock log lines appear over time in both panels with correct
      agent tagging
- [ ] Manual scroll-up pauses auto-scroll; scrolling back to bottom
      resumes it
- [ ] The component's data-source is isolated behind a single
      interface/hook so Unit 14 can swap mock data for a real SSE
      stream with no layout changes
- [ ] `npm run build` passes
