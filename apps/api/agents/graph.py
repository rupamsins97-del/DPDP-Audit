import logging

from apps.api.agents.backend_agent import backend_agent_node
from apps.api.agents.child_safety_agent import child_safety_agent_node
from apps.api.agents.dpr_portal_agent import dpr_portal_agent_node
from apps.api.agents.frontend_agent import frontend_agent_node
from apps.api.agents.incident_management_agent import incident_management_agent_node
from apps.api.agents.policy_agent import policy_agent_node
from apps.api.agents.state import AuditContextState
from apps.api.agents.synthesis_agent import synthesis_init_node, synthesis_reconcile_node
from langgraph.graph import END, START, StateGraph

logger = logging.getLogger(__name__)


def create_audit_graph():
    """Builds and compiles the LangGraph multi-agent DAG state machine (Unit 10)."""
    builder = StateGraph(AuditContextState)

    # 1. Register Nodes
    builder.add_node("synthesis_init", synthesis_init_node)
    builder.add_node("policy_agent", policy_agent_node)
    builder.add_node("frontend_agent", frontend_agent_node)
    builder.add_node("backend_agent", backend_agent_node)
    builder.add_node("incident_management_agent", incident_management_agent_node)
    builder.add_node("child_safety_agent", child_safety_agent_node)
    builder.add_node("dpr_portal_agent", dpr_portal_agent_node)
    builder.add_node("synthesis_reconcile", synthesis_reconcile_node)

    # 2. Wire Edges & Dependencies
    # Entry point
    builder.add_edge(START, "synthesis_init")

    # Policy Agent runs first to extract statutory governance rules
    builder.add_edge("synthesis_init", "policy_agent")

    # Full parallel fan-out to all 5 worker agents from policy_agent
    builder.add_edge("policy_agent", "frontend_agent")
    builder.add_edge("policy_agent", "backend_agent")
    builder.add_edge("policy_agent", "incident_management_agent")
    builder.add_edge("policy_agent", "child_safety_agent")
    builder.add_edge("policy_agent", "dpr_portal_agent")

    # Full parallel fan-in from all 5 workers into synthesis_reconcile
    builder.add_edge("frontend_agent", "synthesis_reconcile")
    builder.add_edge("backend_agent", "synthesis_reconcile")
    builder.add_edge("incident_management_agent", "synthesis_reconcile")
    builder.add_edge("child_safety_agent", "synthesis_reconcile")
    builder.add_edge("dpr_portal_agent", "synthesis_reconcile")

    # Exit point
    builder.add_edge("synthesis_reconcile", END)

    return builder.compile()


# Compiled Singleton Graph
audit_graph = create_audit_graph()
