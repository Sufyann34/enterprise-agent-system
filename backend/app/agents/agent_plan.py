import os
import requests
import time
from typing import Dict, Any
from app.state import AgentState

def call_gemini_with_backoff(prompt: str, system_instruction: str = "") -> str:
    """
    Helper function to call the Gemini API with exponential backoff 
    as required by enterprise guidelines.
    """
    api_key = os.getenv("GEMINI_API_KEY", "")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={api_key}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    if system_instruction:
        payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

    # Exponential backoff: retry up to 5 times
    backoff_delays = [1, 2, 4, 8, 16]
    for attempt, delay in enumerate(backoff_delays):
        try:
            response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
            if response.status_code == 200:
                result = response.json()
                text = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                return text
            elif response.status_code == 429: # Rate limit
                time.sleep(delay)
            else:
                print(f"⚠️ Gemini API returned status code {response.status_code}. Retrying in {delay}s...")
                time.sleep(delay)
        except Exception as e:
            time.sleep(delay)
            
    return "Error: Failed to generate action plan after multiple API retries."

def generate_action_plan_node(state: AgentState) -> Dict[str, Any]:
    """
    Agent 3 (The Manager): Combines retrieved documents and compliance policies
    to generate a clean, comprehensive markdown onboarding action plan.
    """
    print("📋 Agent 3: Synthesizing information and generating action plan...")
    
    query = state.get("user_query", "")
    retrieved_docs = state.get("retrieved_docs", [])
    policies_found = state.get("policies_found", [])
    
    # Format context for the LLM
    docs_context = "\n---\n".join(retrieved_docs) if retrieved_docs else "No specific general documents found."
    policies_context = "\n---\n".join(policies_found) if policies_found else "No specific compliance policies found."
    
    system_prompt = (
        "You are an expert Enterprise Operations Assistant. Your job is to generate "
        "a highly professional, actionable, and compliance-secure onboarding plan. "
        "You must base your plan strictly on the provided Company Documents and Compliance Policies. "
        "Do not hallucinate or make up rules that are not mentioned in the source material."
    )
    
    user_prompt = f"""
USER ORIGINAL REQUEST:
"{query}"

COMPANY DOCUMENTS FOUND:
{docs_context}

STRICT COMPLIANCE POLICIES FOUND:
{policies_context}

Please generate an Onboarding Action Plan formatted in Markdown.
Your response must include:
1. An introductory summary.
2. A structured Timeline (e.g., Prior to Day 1, Day 1, Week 1).
3. Clear highlights of specific compliance flags (such as security rules, deadlines, or MFA instructions) citing where they came from (e.g., "Under Policy Sec-4.2...").
4. A distinct checklist of actions the manager needs to complete.
"""

    action_plan = call_gemini_with_backoff(user_prompt, system_prompt)
    
    print("✅ Agent 3 finished creating the Action Plan.")
    return {
        "action_plan": action_plan,
        "agent_steps": ["agent_plan"]
    }