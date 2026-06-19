import os
import sys
import json
from datetime import datetime

# Add the backend folder to the Python path so we can import our app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, Base, SessionLocal, get_vector_collection
from app.models import Task

def seed_databases():
    print("🚀 Starting database initialization and seeding process...")

    # 1. Create SQL database tables (SQLite)
    print("📁 Creating SQLite tables (tasks, chat_history)...")
    Base.metadata.create_all(bind=engine)
    print("✅ SQLite tables created successfully.")

    # 2. Load seed data from JSON
    seed_file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "seed_data.json"
    )

    if not os.path.exists(seed_file_path):
        print(f"❌ Error: Seed data file not found at {seed_file_path}")
        return

    with open(seed_file_path, "r") as f:
        seed_data = json.load(f)

    # 3. Seed SQL Database (Tasks Table)
    db = SessionLocal()
    try:
        # Clear existing tasks to avoid duplicates on re-runs
        db.query(Task).delete()
        
        print("💾 Seeding tasks into SQL Database...")
        for t_data in seed_data.get("tasks", []):
            task = Task(
                task_description=t_data["task_description"],
                owner=t_data["owner"],
                status=t_data["status"],
                deadline=t_data["deadline"],
                created_at=datetime.strptime(t_data["created_at"], "%Y-%m-%d")
            )
            db.add(task)
        db.commit()
        print(f"✅ SQL Database seeded with {len(seed_data.get('tasks', []))} initial tasks.")
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding SQL database: {e}")
    finally:
        db.close()

    # 4. Seed Vector Database (ChromaDB)
    try:
        print("🧠 Seeding documents into ChromaDB Vector Collection...")
        collection = get_vector_collection()
        
        # We prepare our documents, metadata, and IDs for insertion
        documents = []
        metadatas = []
        ids = []

        # Add Company Docs
        for doc in seed_data.get("company_docs", []):
            documents.append(doc["content"])
            metadatas.append({"title": doc["title"], "category": doc["category"], "type": "company_doc"})
            ids.append(doc["id"])

        # Add Compliance Policies
        for policy in seed_data.get("policies", []):
            documents.append(policy["content"])
            metadatas.append({"title": policy["title"], "category": policy["category"], "type": "policy"})
            ids.append(policy["id"])

        # Upsert documents into ChromaDB (using default Chroma embeddings)
        if documents:
            collection.upsert(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            print(f"✅ ChromaDB seeded with {len(documents)} documents (Company Docs & Policies).")
        else:
            print("⚠️ No documents found to seed in ChromaDB.")

    except Exception as e:
        print(f"❌ Error seeding Vector Database: {e}")

    print("\n🎉 Seeding process completed successfully!")

if __name__ == "__main__":
    seed_databases()