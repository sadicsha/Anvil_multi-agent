import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from langgraph.graph import StateGraph, END

from src.state import AnvilState
from src.agents.data_agent import data_agent
from src.agents.code_agent import code_agent
from src.agents.report_agent import report_agent


# ============================================================
# AGENT NODE WRAPPERS
# ============================================================

def data_node(state):
    return data_agent(state)


def code_node(state):
    return code_agent(state)


def report_node(state):
    return report_agent(state)


# ============================================================
# BUILD ANVIL 3-AGENT PIPELINE
# ============================================================

def build_graph():
    """
    Construct the streamlined 3-Agent Anvil State Machine:
    Data Agent -> Code Agent -> Report Agent -> END
    """
    graph = StateGraph(AnvilState)

    # Register the 3 core agents
    graph.add_node("data_agent", data_node)
    graph.add_node("code_agent", code_node)
    graph.add_node("report_agent", report_node)

    # Entry point
    graph.set_entry_point("data_agent")

    # Linear fast flow
    graph.add_edge("data_agent", "code_agent")
    graph.add_edge("code_agent", "report_agent")
    graph.add_edge("report_agent", END)

    return graph.compile()