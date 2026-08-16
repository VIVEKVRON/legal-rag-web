# StatutIQ: AI-Powered Statutory Intelligence

StatutIQ is an advanced, multilingual Legal Retrieval-Augmented Generation (RAG) web application designed for processing and querying Indian statutory documents. It employs a modern microservices-style backend powered by FastAPI and a highly optimized Vanilla HTML/CSS/JS single-page application (SPA) frontend.

## Features

- **Multilingual Support**: Supports 11 Indian languages (including English, Hindi, Kannada, Tamil, etc.) for both Speech-to-Text (STT) and AI-generated outputs.
- **Adaptive Hybrid Retrieval**: Intelligently routes queries based on language detection. English queries utilize Reciprocal Rank Fusion (RRF) between Dense Vector Search and BM25 Sparse Keyword Search, while regional queries dynamically isolate to pure Dense Vector Search to prevent keyword dilution.
- **Cross-Encoder Reranking**: Re-ranks retrieved candidates using `BAAI/bge-reranker-v2-m3` to guarantee maximum contextual relevance.
- **Generative Synthesis**: Employs the highly capable `Qwen/Qwen2.5-1.5B-Instruct` LLM to generate precise, professional legal responses with strict adherence to cited statutes.
- **Vector Database**: Utilizes a local Qdrant Vector database for lightning-fast semantic retrieval.

## Architecture

StatutIQ operates on a modular, decoupled architecture:

- **Frontend**: ES6 modules (`config.js`, `api.js`, `speech.js`, `state.js`, `render.js`, `view.js`, `main.js`) handling distinct responsibilities from DOM manipulation to Web Speech API integrations.
- **Backend Services (`backend/services/`)**:
  - `embeddings.py`: Generates dense vectors using `BAAI/bge-m3`.
  - `bm25_search.py`: Handles token-based sparse retrieval.
  - `vector_store.py`: Interfaces with the Qdrant database.
  - `hybrid_fusion.py`: Merges multi-vector searches using mathematical RRF logic.
  - `reranker.py`: Employs transformer models to evaluate query-document pairs.
  - `llm_generator.py`: Generates grounded answers with strict system prompts.
  - `rag_orchestrator.py`: The brain that coordinates the entire RAG pipeline dynamically based on heuristics.

## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/VIVEKVRON/legal-rag-web.git
   cd legal-rag-web
   ```

2. **Set up a Python Virtual Environment:**
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate  # Windows
   source .venv/bin/activate # Linux/Mac
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Server:**
   The backend relies on the FastAPI `lifespan` manager to load machine learning models into memory exactly once upon server startup. Start the server from the project root:
   ```bash
   python -m uvicorn backend.main:app
   ```

5. **Access the Application:**
   Open your browser and navigate to `http://localhost:8000`.

## Disclaimer

*StatutIQ is an AI research tool and is not a substitute for formal legal counsel. Always verify statutory references and seek professional legal advice.*
