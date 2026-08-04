# backend/ingestion.py
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import json

# 1. Define Data (Paste your full legal_documents list here)
legal_documents = [
    {
        "doc_id": "RENT_CONTROL_ACT_SEC_10",
        "law_type": "civil",
        "jurisdiction": "Karnataka",
        "language": "en",
        "text": "Section 10: Eviction of tenants.\nA landlord may not evict a tenant except on one or more of the following grounds:\n\n(a) that the tenant has neither paid nor tendered the whole of the arrears of the rent legally payable by him for two consecutive months;\n\n(b) that the tenant has without the landlord's consent given in writing, erected on the premises any permanent structure."
    }
    # ... add your other documents ...
]

# 2. Context-Aware Chunker
def chunk_legal_documents_v2(documents):
    chunks = []
    for doc in documents:
        raw_chunks = [chunk.strip() for doc_chunk in doc["text"].split('\n\n') if (chunk := doc_chunk.strip())]
        parent_context = raw_chunks[0] 
        for i, text_chunk in enumerate(raw_chunks):
            final_text = text_chunk if i == 0 else f"{parent_context}\n{text_chunk}"
            chunks.append({
                "chunk_id": f"{doc['doc_id']}_chunk_{i}",
                "doc_id": doc["doc_id"],
                "text": final_text 
            })
    return chunks

# 3. Setup Qdrant to save to disk
client = QdrantClient(path="./vector_db") # <-- CRITICAL CHANGE
COLLECTION_NAME = "legal_rag_collection"

client.recreate_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
)

# 4. Embed and Upload
print("Loading Embedding Model...")
embedding_model = SentenceTransformer("BAAI/bge-m3", device="cpu") # Use "cuda" if you have a local Nvidia GPU

print("Chunking and Vectorizing...")
chunks = chunk_legal_documents_v2(legal_documents)
points = [
    PointStruct(id=idx, vector=embedding_model.encode(chunk["text"]).tolist(), payload=chunk)
    for idx, chunk in enumerate(chunks)
]

client.upsert(collection_name=COLLECTION_NAME, points=points)
print("Ingestion Complete! Database saved to ./vector_db")