import os
from typing import Dict, Any
from app.state import AgentState
from app.database import get_vector_collection

def retrieve_company_docs_node(state: AgentState) -> Dict[str, Any]:
    """
    Agent 1 (The Librarian): Semantic-searches our ChromaDB vector database 
    for relevant general company guidelines, guides, and manuals.
    """
    print("🔍 Agent 1: Searching company document database...")
    
    query = state.get("user_query", "")
    if not query:
        return {"retrieved_docs": [], "agent_steps": ["agent_docs"]}

    try:
        # Connect to our persistent ChromaDB collection
        collection = get_vector_collection()
        
        # Query the collection specifically for general company docs.
        # We filter the metadata where type is 'company_doc' to make sure
        # this agent only retrieves general knowledge, not legal policies.
        results = collection.query(
            query_texts=[query],
            n_results=2,
            where={"type": "company_doc"}
        )
        
        retrieved = []
        if results and "documents" in results and results["documents"]:
            # ChromaDB returns a nested list of documents
            for doc_list in results["documents"]:
                for doc in doc_list:
                    retrieved.append(doc)
        
        print(f"✅ Agent 1 retrieved {len(retrieved)} relevant company document(s).")
        return {
            "retrieved_docs": retrieved,
            "agent_steps": ["agent_docs"]
        }
    except Exception as e:
        print(f"❌ Agent 1 Error: {str(e)}")
        return {
            "retrieved_docs": [f"Error retrieving company docs: {str(e)}"],
            "agent_steps": ["agent_docs"]
        }