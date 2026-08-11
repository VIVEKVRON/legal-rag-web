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
import re

def chunk_legal_documents_v2(documents):
    chunks = []
    chunk_size = 512
    overlap = 128
    
    for doc in documents:
        text = doc["text"]
        doc_id = doc["doc_id"]
        
        words = text.split()
        if not words:
            continue
            
        # Detect sections to maintain structural context
        sections = []
        for match in re.finditer(r"(Section\s+\d+[A-Z]*|Article\s+\d+[A-Z]*|Schedule\s+\d+[A-Z]*)", text, re.IGNORECASE):
            sections.append((match.start(), match.group(1).strip()))
            
        def get_current_section(char_idx):
            current_sec = "General Provisions"
            for start_idx, sec_name in sections:
                if start_idx <= char_idx:
                    current_sec = sec_name
                else:
                    break
            return current_sec

        i = 0
        chunk_idx = 0
        while i < len(words):
            chunk_words = words[i:i + chunk_size]
            chunk_text = " ".join(chunk_words)
            
            snippet = " ".join(chunk_words[:10])
            char_idx = text.find(snippet)
            if char_idx == -1: char_idx = 0
            
            current_section = get_current_section(char_idx)
            
            metadata_header = f"Act: {doc_id} | Section: {current_section}\n"
            final_text = metadata_header + chunk_text
            
            chunks.append({
                "chunk_id": f"{doc_id}_chunk_{chunk_idx}",
                "doc_id": doc_id,
                "text": final_text
            })
            
            chunk_idx += 1
            i += (chunk_size - overlap)
            
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