# Enterprise RAG with Role-Based Access Control (RBAC)

A secure AI assistant that enforces data governance — employees only see 
documents they're authorised to access, enforced at the database level.

## How it works
- Documents are embedded and stored with clearance metadata (intern/manager/exec)
- On every query, a metadata pre-filter runs BEFORE vector search
- Restricted documents are never retrieved — not just hidden, physically blocked
- JWT authentication verifies every request

## Tech Stack
FastAPI · pgvector · PostgreSQL · Google Gemini API · Docker · JWT

## Setup
1. Clone the repo
2. Copy `.env.example` to `.env` and fill in your keys
3. Get a free Gemini API key at aistudio.google.com
4. Run: `docker-compose up -d`
5. Run: `py ingest.py`
6. Run: `py -m uvicorn main:app --reload`
7. Open `index.html` in browser or visit `http://localhost:8000/docs`

## Test users
| User  | Password | Clearance |
|-------|----------|-----------|
| alice | pass123  | intern    |
| carol | pass789  | manager   |
| bob   | pass456  | exec      |

## Demo
Ask "What are the engineering manager salaries?" as alice → blocked.
Ask the same as bob → full answer. Same question, different access levels.