# Unit 05 — LangGraph Orchestrator Skeleton

## Goal

Build the LangGraph state machine and event-bus wiring — with a
`synthesis_agent` stub node that can dispatch to placeholder worker
nodes and report back — so Units 06–10 each implement one real node
against an already-working DAG instead of building the DAG piecemeal.

## Design

No UI. This is the "Agentic Architecture & Orchestration Model"
section of the PRD (`synthesis_agent` as leader, six workers in
parallel) made real as code, minus the workers' actual reasoning.

## Implementation

1. Define the LangGraph graph with one node per agent named exactly
   as in the v3 docs: `synthesis_agent`, `policy_agent`,
   `frontend_agent`, `backend_agent`, `incident_management_agent`,
   `child_safety_agent`, `dpr_portal_agent`. Each non-synthesis node
   is a no-op stub in this unit that returns an empty findings list
   for its role.
2. `synthesis_agent` node: on entry, dispatches to `policy_agent`
   first (governance extraction must complete first per the Phase
   2→3 ordering in `agent-flow-and-interagent-bus-v3.md`), then
   fans out to `frontend_agent`/`backend_agent` in parallel, then to
   the three domain-extension agents, then aggregates.
3. Implement the event-bus client (`apps/api/tools/event_bus.py`)
   wrapping Pub/Sub or Redis (pick one and record the decision in
   `progress-tracker.md` — the v3 docs list both as options); emit
   `GOVERNANCE_RULES_READY` after `policy_agent` completes, exactly
   as named in the v3 docs, so Units 08/07 can subscribe to it later.
4. Persist `AuditContextState` checkpoints to the `audits` row
   (`status` transitions) as the graph progresses — this is what
   Unit 04's SSE stub and Unit 14's real stream will read from.
5. Wire `POST /audits` (Unit 04) to actually invoke this graph as a
   background task (not awaited in the request handler — Invariant
   1) instead of only writing a row.

## Dependencies

- `langgraph`, `langchain-core` (or the minimal subset LangGraph
  needs), a Pub/Sub or Redis client library per the decision above.

## Verification Checklist

- [ ] Submitting an audit runs the full graph end to end with every
      node a no-op, and `audits.status` transitions to `COMPLETED`
      with an empty findings set
- [ ] `GOVERNANCE_RULES_READY` is emitted on the event bus after the
      `policy_agent` stub node runs, and is observable by a test
      subscriber
- [ ] The graph genuinely parallelizes `frontend_agent` and
      `backend_agent` (verified by timing, not just by DAG shape)
- [ ] The request handler for `POST /audits` returns before the graph
      finishes running (Invariant 1)
- [ ] The Pub/Sub-vs-Redis decision is recorded in
      `progress-tracker.md` under Architecture Decisions
