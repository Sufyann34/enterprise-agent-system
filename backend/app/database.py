import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import chromadb
from chromadb.config import Settings

# --- SQL Database Setup (SQLite for zero-config development) ---
DATABASE_URL = "sqlite:///./enterprise_knowledge.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Vector Database Setup (ChromaDB) ---
# We store the vector database inside a folder in our backend directory
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chroma_db")

chroma_client = chromadb.PersistentClient(path=DB_PATH)

def get_db():
    """Dependency helper to get SQL database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_vector_collection():
    """Gets or creates the vector collection for our company documents"""
    return chroma_client.get_or_create_collection(name="company_knowledge")