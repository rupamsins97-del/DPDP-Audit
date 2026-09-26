# Unit 08 — `frontend_agent` Browser Automation

## Goal

Implement Stagehand/CDP-driven live-site auditing: pre-consent
network interception, AXTree consent-UI verification, and
consent-withdrawal parity testing (FR-2.1 – FR-2.4).

## Design

Feeds the "Live Browser Execution" panel with narration like
"Intercepting network...", "Clicking consent modal..." exactly as
shown in the master-prompts UI mock.

## Implementation

1. Set `apps/api/agents/prompts/frontend_agent.md` to the exact
   system prompt from `master-prompts-and-ui-ux-v3.md` §2.3,
   verbatim.
2. Subscribe to `GOVERNANCE_RULES_READY` (from Unit 06) before
   starting — this agent needs `declared_trackers` from
   `governance_promises` to know what to watch for.
3. FR-2.1: attach the CDP network-request hook from
   `agent-flow-and-interagent-bus-v3.md` §3.2 — flag any tracker
   domain request firing before consent as CRITICAL, Section 6(1).
4. FR-2.4: before navigation, inspect response headers (`CF-RAY`,
   `Server: DataDome`, `X-Akamai`); if anti-bot protection is
   detected, route the CDP session through Scrapfly Unblocker.
5. FR-2.2: use AXTree extraction (not raw DOM) to verify consent
   options are unbundled, unchecked by default, and available in the
   declared languages from `governance_promises`.
6. FR-2.3: measure and compare the click/step count to give vs.
   withdraw consent; flag any asymmetry under Rule 3(c)(i).
7. Cross-reference step: if a tracker in `declared_trackers` (from
   the Privacy Policy) fires pre-consent, this is the "Statutory
   Misrepresentation" case the `synthesis_agent` prompt calls out —
   emit the raw observation here; `synthesis_agent` (Unit 10) does
   the cross-referencing and CRITICAL upgrade.
8. Every finding cites `Section 6(1)` or `Rule 3(c)(i)` as
   appropriate (Invariant 3).

## Dependencies

- Stagehand (on Playwright), Scrapfly Unblocker API client, a CDP
  network-domain allowlist/denylist for known tracker domains (Meta
  Pixel, Google Analytics, ByteDance, etc.).

## Verification Checklist

- [ ] A test page with a pre-consent tracker script is correctly
      flagged CRITICAL under Section 6(1)
- [ ] A test page with a pre-checked consent box is flagged under the
      unbundled-consent requirement
- [ ] Withdrawal-parity test correctly flags a page requiring more
      steps to withdraw than to give consent
- [ ] Anti-bot-protected test target is successfully routed through
      Scrapfly and still produces findings
- [ ] AXTree extraction is used for consent-UI inspection (not raw
      HTML DOM parsing) — confirmed by code review against FR-2.2
