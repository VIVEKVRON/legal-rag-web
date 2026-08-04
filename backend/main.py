from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os

# We now only need the query processing function from the engine
from rag_engine import process_query

app = FastAPI(title="Legal RAG API")

# Simplified request model - target_doc_id is gone
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str
    sources: list

@app.post("/api/ask", response_model=QueryResponse)
async def ask_legal_question(request: QueryRequest):
    try:
        # Pass only the query to the backend engine
        result = process_query(request.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get the absolute path to the frontend folder
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

# Serve the index.html on the root URL
@app.get("/")
async def serve_frontend():
    return FileResponse(os.path.join(frontend_dir, "index.html"))

# Mount the rest of the frontend folder to serve static files (like app.js and style.css)
app.mount("/", StaticFiles(directory=frontend_dir), name="frontend")