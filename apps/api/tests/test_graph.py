import asyncio
import tempfile
from contextlib import contextmanager
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from apps.api.agents.graph import audit_graph
from apps.api.agents.runner import run_audit_pipeline
from apps.api.agents.state import AuditContextState
from apps.api.tools.event_bus import get_event_bus


@pytest.mark.asyncio
async def test_audit_graph_runs_end_to_end() -> None:
    """Check that the full graph executes end to end and transitions to COMPLETED."""
    audit_id = str(uuid4())
    org_id = str(uuid4())

    initial_state: AuditContextState = {
        "audit_id": audit_id,
        "organization_id": org_id,
        "project_name": "Test Run",
        "target_url": "https://example.com",
        "repository_url": None,
        "framework": "BOTH",
        "status": "IN_PROGRESS",
        "governance_promises": [],
        "findings": [],
        "generated_patches": [],
        "compliance_score": None,
        "state_hash": None,
        "error": None,
    }

    final_state = await audit_graph.ainvoke(initial_state)

    assert final_state["status"] == "COMPLETED"
    assert final_state["compliance_score"] is not None
    assert 0 <= final_state["compliance_score"] <= 100
    assert final_state["state_hash"] is not None
    assert isinstance(final_state["findings"], list)


@pytest.mark.asyncio
async def test_governance_rules_ready_event_emitted() -> None:
    """Check that policy_agent emits GOVERNANCE_RULES_READY and it is received by subscribers."""
    audit_id = str(uuid4())
    org_id = str(uuid4())
    event_bus = get_event_bus()

    received_events = []

    async def subscriber():
        async for msg in event_bus.subscribe("GOVERNANCE_RULES_READY"):
            received_events.append(msg)
            break

    sub_task = asyncio.create_task(subscriber())
    await asyncio.sleep(0.01)

    initial_state: AuditContextState = {
        "audit_id": audit_id,
        "organization_id": org_id,
        "project_name": "Event Bus Test",
        "target_url": "https://example.com",
        "repository_url": None,
        "framework": "BOTH",
        "status": "IN_PROGRESS",
        "governance_promises": [],
        "findings": [],
        "generated_patches": [],
        "compliance_score": None,
        "state_hash": None,
        "error": None,
    }

    await audit_graph.ainvoke(initial_state)
    await asyncio.wait_for(sub_task, timeout=2.0)

    assert len(received_events) == 1
    assert received_events[0]["event"] == "GOVERNANCE_RULES_READY"
    assert received_events[0]["payload"]["audit_id"] == audit_id


@pytest.mark.asyncio
async def test_graph_parallelizes_frontend_and_backend_nodes() -> None:
    """Verify that frontend_agent and backend_agent run concurrently via timing."""
    audit_id = str(uuid4())
    org_id = str(uuid4())

    initial_state: AuditContextState = {
        "audit_id": audit_id,
        "organization_id": org_id,
        "project_name": "Parallelism Test",
        "target_url": "https://example.com",
        "repository_url": "https://github.com/test/repo",
        "framework": "BOTH",
        "status": "IN_PROGRESS",
        "governance_promises": [],
        "findings": [],
        "generated_patches": [],
        "compliance_score": None,
        "state_hash": None,
        "error": None,
    }

    @contextmanager
    def mock_ephemeral_clone(url: str | None):
        with tempfile.TemporaryDirectory() as td:
            yield td

    with patch("apps.api.agents.backend_agent.ephemeral_clone", mock_ephemeral_clone):
        start = datetime.now(UTC)
        await audit_graph.ainvoke(initial_state)
        duration = (datetime.now(UTC) - start).total_seconds()

    # The run should finish in under 1.0s in local test environment
    assert duration < 1.0


@pytest.mark.asyncio
async def test_runner_updates_supabase_on_completion() -> None:
    """Check that run_audit_pipeline updates the Supabase audits row to COMPLETED."""
    audit_id = str(uuid4())
    org_id = str(uuid4())

    mock_supabase = MagicMock()
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = (
        MagicMock(data=[{"audit_id": audit_id, "status": "COMPLETED"}])
    )

    final_state = await run_audit_pipeline(
        audit_id=audit_id,
        organization_id=org_id,
        project_name="Runner Test",
        target_url="https://example.com",
        repository_url=None,
        framework="BOTH",
        supabase=mock_supabase,
    )

    assert final_state["status"] == "COMPLETED"
    mock_supabase.table.assert_called_with("audits")
