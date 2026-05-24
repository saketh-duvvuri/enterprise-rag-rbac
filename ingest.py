import os
import psycopg2
import psycopg2.extras

from google import genai



client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
DATABASE_URL = os.getenv("DATABASE_URL")

def get_embedding(text: str) -> list:
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )
    return result.embeddings[0].values

def load_txt_file(filepath: str) -> list:
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return [line.strip() for line in lines if line.strip()]

def ingest_data():
    conn = psycopg2.connect(DATABASE_URL)
    cur  = conn.cursor()
    print("✅ Connected to database!")

    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    cur.execute("DROP TABLE IF EXISTS documents;")
    cur.execute("""
        CREATE TABLE documents (
            id        SERIAL PRIMARY KEY,
            content   TEXT,
            metadata  JSONB,
            embedding vector(3072)
        );
    """)
    print("📦 Created fresh table with vector(768)")

    intern_chunks  = load_txt_file("policy_intern.txt")
    manager_chunks = load_txt_file("policy_manager.txt")   # ← add this
    exec_chunks    = load_txt_file("policy_exec.txt")

    all_documents = (
    [(c, "intern")  for c in intern_chunks]  +
    [(c, "manager") for c in manager_chunks] +   # ← add this
    [(c, "exec")    for c in exec_chunks]
    )

    print(f"\n📄 Ingesting {len(all_documents)} chunks...\n")

    for i, (text, clearance) in enumerate(all_documents):
        print(f"  [{i+1}/{len(all_documents)}] {text[:55]}...")
        embedding = get_embedding(text)
        cur.execute(
            "INSERT INTO documents (content, metadata, embedding) VALUES (%s, %s, %s)",
            (text, psycopg2.extras.Json({"clearance": clearance}), embedding)
        )

    conn.commit()
    cur.close()
    conn.close()
    print("\n🎉 All documents ingested successfully!")

if __name__ == "__main__":
    ingest_data()