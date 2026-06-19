import os
from typing import Dict, Any
from app.state import AgentState
from app.database import get_vector_collection

def find_policies_node(state: AgentState) -> Dict[str, Any]:
    """
    Agent 2 (The Compliance Officer): Semantic-searches our ChromaDB vector database 
    for strict company policies, regulatory guidelines, and compliance rules.
    """
    print("⚖️ Agent 2: Searching corporate policy database...")
    
    query = state.get("user_query", "")
    if not query:
        return {"policies_found": [], "agent_steps": ["agent_policy"]}

    try:
        # Connect to our persistent ChromaDB collection
        collection = get_vector_collection()
        
        # Query the collection specifically for policy docs.
        # We filter the metadata where type is 'policy' to make sure
        # this agent only retrieves regulatory requirements.
        results = collection.query(
            query_texts=[query],
            n_results=2,
            where={"type": "policy"}
        )
        
        policies = []
        if results and "documents" in results and results["documents"]:
            # ChromaDB returns a nested list of documents
            for doc_list in results["documents"]:
                for doc in doc_list:
                    policies.append(doc)
        
        print(f"✅ Agent 2 found {len(policies)} applicable policy snippet(s).")
        return {
            "policies_found": policies,
            "agent_steps": ["agent_policy"]
        }
    except Exception as e:
        print(f"❌ Agent 2 Error: {str(e)}")
        return {
            "policies_found": [f"Error finding compliance policies: {str(e)}"],
            "agent_steps": ["agent_policy"]
        }