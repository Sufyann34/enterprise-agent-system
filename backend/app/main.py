import os
import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

# Import our database, models, and LangGraph workflow
from app.database import get_db, engine, Base
from app.models import Task, ChatHistory
from app.graph import app_graph

# Initialize database tables on server startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Enterprise Multi-Agent Knowledge API",
    description="Backend API powering our LangGraph and ChromaDB task-force system."
)

# Enable CORS so our frontend index.html can seamlessly call our backend API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits access from any origin (ideal for local development)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Schemas for Input Validation ---
class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = "default_session"

class TaskUpdate(BaseModel):
    status: str  # Pending, In Progress, Completed, Blocked

class TaskResponse(BaseModel):
    id: int
    task_description: str
    owner: str
    status: str
    deadline: Optional[str]
    created_at: str

    class Config:
        from_attributes = True

# --- API Endpoints ---

@app.get("/")
def read_root():
    return {"status": "online", "system": "Multi-Agent Enterprise Knowledge Base API"}

@app.post("/api/chat")
def run_agent_workflow(payload: QueryRequest, db: Session = Depends(get_db)):
    """
    Triggers the LangGraph state machine. Passes the user query through all 4 agents
    sequentially, saves history, and returns the final action plan and updated tasks.
    """
    user_query = payload.query.strip()
    session_id = payload.session_id
    
    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
        
    # 1. Check if Gemini API key exists
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(
            status_code=500, 
            detail="GEMINI_API_KEY environment variable is missing. Please add it to your .env file."
        )

    # 2. Save User Message to SQL Short-term Chat History
    user_msg = ChatHistory(session_id=session_id, role="user", content=user_query)
    db.add(user_msg)
    db.commit()

    print(f"\n📥 New Request Received: '{user_query}'")
    print("🕸️ Invoking LangGraph Agent workflow state machine...")

    # 3. Formulate the starting state dictionary for our agents
    initial_state = {
        "user_query": user_query,
        "messages": [{"role": "user", "content": user_query}],
        "retrieved_docs": [],
        "policies_found": [],
        "action_plan": "",
        "pending_tasks": [],
        "agent_steps": []
    }

    try:
        # Run the entire Graph! Control flows through Agent 1 -> Agent 2 -> Agent 3 -> Agent 4
        final_state = app_graph.invoke(initial_state)
        
        # 4. Save Assistant Action Plan Response to Short-term Memory
        final_plan = final_state.get("action_plan", "No action plan could be generated.")
        assistant_msg = ChatHistory(session_id=session_id, role="assistant", content=final_plan)
        db.add(assistant_msg)
        db.commit()

        # 5. Return the full updated state for our front-end visualization panels
        return {
            "session_id": session_id,
            "user_query": user_query,
            "retrieved_docs": final_state.get("retrieved_docs", []),
            "policies_found": final_state.get("policies_found", []),
            "action_plan": final_plan,
            "pending_tasks": final_state.get("pending_tasks", []),
            "agent_steps": final_state.get("agent_steps", [])
        }

    except Exception as e:
        print(f"❌ Error during graph invocation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Agent workflow failed: {str(e)}")

@app.get("/api/tasks")
def list_all_tasks(db: Session = Depends(get_db)):
    """
    Fetches the persistent Unsolved Tasks Ledger (Agent 4 output)
    from SQLite so the frontend can display them.
    """
    tasks = db.query(Task).order_by(Task.created_at.desc()).all()
    return tasks

@app.put("/api/tasks/{task_id}")
def update_task_status(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    """
    Allows human-in-the-loop actions: toggle, edit, or resolve
    tasks from the dashboard.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    task.status = payload.status
    db.commit()
    return {"message": "Task status updated successfully", "task_id": task_id, "new_status": task.status}

if __name__ == "__main__":
    # Runs FastAPI server on localhost:8000 when executed directly
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)