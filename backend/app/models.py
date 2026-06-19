from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from .database import Base

class Task(Base):
    """Table to store and track unresolved tasks (managed by Agent 4)"""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_description = Column(String, nullable=False)
    owner = Column(String, default="Hiring Manager")
    status = Column(String, default="Pending")  # Pending, In Progress, Completed, Blocked
    deadline = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ChatHistory(Base):
    """Table to store conversation history for short-term memory"""
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)