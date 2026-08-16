from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from backend.schemas import QueryRequest, QueryResponse
from backend.services.rag_orchestrator import RAGOrchestrator

orchestrator = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Initializing StatutIQ Backend Models & Services...")
    global orchestrator
    orchestrator = RAGOrchestrator()
    orchestrator.initialize_indexes()
    print("StatutIQ Backend is READY.")
    yield
    # Shutdown
    print("Shutting down StatutIQ Backend...")
    orchestrator = None

app = FastAPI(lifespan=lifespan)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/ask", response_model=QueryResponse)
def ask_question(request: QueryRequest):
    result = orchestrator.process_query(request.query)
    return result

# Serve static frontend
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")