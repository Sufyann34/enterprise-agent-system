from typing import TypedDict, List, Dict, Any, Annotated
import operator

def merge_messages(left: List[Dict[str, Any]], right: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Helper reducer to append new messages to our short-term chat history"""
    return left + right

class AgentState(TypedDict):
    """
    The shared state (clipboard) passed between all 4 agents in LangGraph.
    This manages both the data retrieved and the communication context.
    """
    # The original query typed by the user
    user_query: str
    
    # Short-term memory: chat log of the conversation
    messages: Annotated[List[Dict[str, str]], merge_messages]
    
    # Agent 1 (Retriever) output: raw text of documents retrieved from Vector DB
    retrieved_docs: List[str]
    
    # Agent 2 (Policy Finder) output: compliance and HR policies found
    policies_found: List[str]
    
    # Agent 3 (Plan Generator) output: the final markdown action plan
    action_plan: str
    
    # Agent 4 (Task Tracker) output: list of newly identified unsolved tasks
    pending_tasks: List[Dict[str, Any]]
    
    # Keeps track of which agents have executed (for our frontend live map)
    agent_steps: List[str]