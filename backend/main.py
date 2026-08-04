from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import fitz  # PyMuPDF
import os

from qdrant_client.models import PointStruct
from rag_engine import process_query, chunk_legal_documents_v2, embedding_model, client, COLLECTION_NAME

app = FastAPI(title="Legal RAG API")

class QueryRequest(BaseModel):
    query: str
    target_doc_id: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    sources: list

@app.post("/api/ask", response_model=QueryResponse)
async def ask_legal_question(request: QueryRequest):
    try:
        result = process_query(request.query, request.target_doc_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_legal_document(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    try:
        # 1. Read the PDF file from memory
        file_bytes = await file.read()
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        
        # 2. Extract text from all pages
        full_text = ""
        for page in doc:
            full_text += page.get_text() + "\n\n"
            
        if not full_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from this PDF.")

        # 3. Format as a dictionary for your chunker
        doc_id = file.filename.replace(".pdf", "").replace(" ", "_")
        raw_doc = [{
            "doc_id": doc_id,
            "text": full_text
        }]
        
        # 4. Chunk and Vectorize 
        chunks = chunk_legal_documents_v2(raw_doc)
        
        # Determine starting ID for Qdrant to avoid overwriting 
        current_count = client.count(collection_name=COLLECTION_NAME).count
        
        points = [
            PointStruct(
                id=current_count + idx, 
                vector=embedding_model.encode(chunk["text"]).tolist(), 
                payload=chunk
            )
            for idx, chunk in enumerate(chunks)
        ]
        
        # 5. Save to database
        client.upsert(collection_name=COLLECTION_NAME, points=points)
        
        return {
            "message": f"Successfully ingested {file.filename} into the database!",
            "doc_id": doc_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")

# Get the absolute path to the frontend folder
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

# Serve the index.html on the root URL
@app.get("/")
async def serve_frontend():
    return FileResponse(os.path.join(frontend_dir, "index.html"))

# Mount the rest of the frontend folder to serve static files (like app.js and style.css)
app.mount("/", StaticFiles(directory=frontend_dir), name="frontend")