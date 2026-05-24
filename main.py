from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
import os
from dotenv import load_dotenv
from google import genai

from auth import authenticate_user, create_token, decode_token, get_allowed_clearances

# Setup
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI(title="Enterprise RAG with RBAC")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Models
class LoginRequest(BaseModel):
    username: str
    password: str

class QueryRequest(BaseModel):
    question: str

# Embedding function
def get_embedding(text: str) -> list:
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )
    return result.embeddings[0].values

# Routes
@app.get("/")
def home():
    return {"status": "running", "tip": "Visit /docs to test endpoints"}

@app.post("/login")
def login(req: LoginRequest):
    user = authenticate_user(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Wrong username or password")
    token = create_token(user["username"], user["clearance"])
    return {"token": token, "username": user["username"], "clearance": user["clearance"]}

@app.post("/ask")
def ask(req: QueryRequest, authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Use: Bearer <token>")
    
    token = authorization.replace("Bearer ", "").strip()
    
    try:
        user_data = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    username = user_data["username"]
    user_clearance = user_data["clearance"]
    allowed = get_allowed_clearances(user_clearance)

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        placeholders = ",".join(["%s"] * len(allowed))
        query_embedding = get_embedding(req.question)

        cur.execute(f"""
            SELECT content, metadata->>'clearance' AS clearance
            FROM documents
            WHERE metadata->>'clearance' IN ({placeholders})
            ORDER BY embedding <=> %s::vector
            LIMIT 3;
        """, allowed + [query_embedding])

        results = cur.fetchall()
        cur.close()
        conn.close()

        if not results:
            return {
                "username": username,
                "clearance": user_clearance,
                "answer": "This information is not available at your access level.",
                "docs_used": []
            }

        context = "\n\n".join([f"[{row[1].upper()}]: {row[0]}" for row in results])
        docs_used = [{"preview": row[0][:60], "clearance": row[1]} for row in results]

        # Generate answer with Gemini
        prompt = f"""You are a secure corporate assistant.
Answer ONLY using the context below. If the answer is not in the context, say 'This information is not available at your access level.'

Context:
{context}

Question: {req.question}"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return {
            "username": username,
            "clearance": user_clearance,
            "answer": response.text,
            "docs_used": docs_used
        }

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/me")
def me(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "").strip()
    try:
        return decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")