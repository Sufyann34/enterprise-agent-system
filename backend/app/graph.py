from langgraph.graph import StateGraph, END
from app.state import AgentState
from app.agents.agent_docs import retrieve_company_docs_node
from app.agents.agent_policy import find_policies_node
from app.agents.agent_plan import generate_action_plan_node
from app.agents.agent_tasks import track_unsolved_tasks_node

def create_workflow():
    """
    Constructs the LangGraph state machine graph, connecting all 4 agents
    to process a user query step-by-step.
    """
    # 1. Initialize the StateGraph with our shared AgentState schema
    workflow = StateGraph(AgentState)

    # 2. Add our 4 agents as graph nodes
    workflow.add_node("agent_docs", retrieve_company_docs_node)
    workflow.add_node("agent_policy", find_policies_node)
    workflow.add_node("agent_plan", generate_action_plan_node)
    workflow.add_node("agent_tasks", track_unsolved_tasks_node)

    # 3. Define the connections (edges)
    # The flow starts at Agent 1, moves to Agent 2, then Agent 3, and ends at Agent 4
    workflow.set_entry_point("agent_docs")
    
    workflow.add_edge("agent_docs", "agent_policy")
    workflow.add_edge("agent_policy", "agent_plan")
    workflow.add_edge("agent_plan", "agent_tasks")
    
    # After Agent 4 tracks and saves the tasks, the graph run is completed (END)
    workflow.add_edge("agent_tasks", END)

    # 4. Compile the graph into an executable runnable
    return workflow.compile()

# Generate a compiled instance of our graph to be imported by the API layer
app_graph = create_workflow()