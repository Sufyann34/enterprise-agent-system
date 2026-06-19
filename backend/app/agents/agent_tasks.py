import os
import json
import requests
import time
from typing import Dict, Any
from app.state import AgentState
from app.database import SessionLocal
from app.models import Task

def call_gemini_json_with_backoff(prompt: str, system_instruction: str = "") -> str:
    """
    Calls the Gemini API requesting a structured JSON response 
    with exponential backoff for enterprise reliability.
    """
    api_key = os.getenv("GEMINI_API_KEY", "")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={api_key}"
    
    # Configure Gemini payload to enforce a structured JSON schema
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "tasks": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "task_description": {"type": "STRING"},
                                "owner": {"type": "STRING"},
                                "status": {"type": "STRING"},
                                "deadline": {"type": "STRING"}
                            },
                            "required": ["task_description", "owner", "status", "deadline"]
                        }
                    }
                },
                "required": ["tasks"]
            }
        }
    }
    
    if system_instruction:
        payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

    backoff_delays = [1, 2, 4, 8, 16]
    for attempt, delay in enumerate(backoff_delays):
        try:
            response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
            if response.status_code == 200:
                result = response.json()
                text = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                return text
            else:
                print(f"⚠️ Gemini Tasks API returned status code {response.status_code}. Retrying in {delay}s...")
                time.sleep(delay)
        except Exception as e:
            time.sleep(delay)
            
    return '{"tasks": []}'

def track_unsolved_tasks_node(state: AgentState) -> Dict[str, Any]:
    """
    Agent 4 (The Auditor): Parses the Markdown action plan from Agent 3,
    extracts actionable tasks, and commits them to the SQLite database.
    """
    print("📋 Agent 4: Inspecting action plan for pending tasks...")
    
    action_plan = state.get("action_plan", "")
    if not action_plan:
        return {"pending_tasks": [], "agent_steps": ["agent_tasks"]}

    system_instruction = (
        "You are an AI Operational Audit Assistant. Your task is to analyze the provided "
        "Onboarding Action Plan and extract concrete, actionable tasks that a manager or team member "
        "needs to perform. You must format the output matching the requested JSON Schema strictly."
    )
    
    prompt = f"""
Please extract all incomplete or required pending tasks from this Action Plan:

ACTION PLAN:
\"\"\"
{action_plan}
\"\"\"

For each task, provide:
- 'task_description': What needs to be done.
- 'owner': Who is responsible (e.g., 'Hiring Manager', 'IT Specialist', or 'New Hire'). Default to 'Hiring Manager' if unspecified.
- 'status': Set default status to 'Pending'.
- 'deadline': Extract any specific date or timeline mention (e.g. '2 days before start', 'Day 1').
"""

    json_response_str = call_gemini_json_with_backoff(prompt, system_instruction)
    
    tasks_to_save = []
    try:
        parsed_data = json.loads(json_response_str)
        tasks_to_save = parsed_data.get("tasks", [])
    except Exception as e:
        print(f"❌ Agent 4 failed to parse structured JSON from LLM: {e}")

    # Commit extracted tasks directly to our persistent SQL database
    saved_tasks_list = []
    if tasks_to_save:
        db = SessionLocal()
        try:
            print(f"💾 Agent 4: Committing {len(tasks_to_save)} extracted tasks to SQLite...")
            for item in tasks_to_save:
                # Create a database record for each task
                db_task = Task(
                    task_description=item["task_description"],
                    owner=item["owner"],
                    status=item["status"],
                    deadline=item["deadline"]
                )
                db.add(db_task)
                
            db.commit()
            
            # Read back tasks so we can save their structured representations into the State
            print("✅ Agent 4: Tasks successfully committed.")
            for item in tasks_to_save:
                saved_tasks_list.append({
                    "task_description": item["task_description"],
                    "owner": item["owner"],
                    "status": item["status"],
                    "deadline": item["deadline"]
                })
        except Exception as db_err:
            db.rollback()
            print(f"❌ Agent 4 database write error: {db_err}")
        finally:
            db.close()
    else:
        print("⚠️ Agent 4: No new pending tasks were identified in the action plan.")

    return {
        "pending_tasks": saved_tasks_list,
        "agent_steps": ["agent_tasks"]
    }