import os
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# 1. Connect to Database & Load Embedding Model
COLLECTION_NAME = "legal_rag_collection"
client = QdrantClient(path="./vector_db")
print("Loading embedding model...")
embedding_model = SentenceTransformer("BAAI/bge-m3", device="cpu")

# 2. Ensure Collection Exists
if not client.collection_exists(collection_name=COLLECTION_NAME):
    print("Creating new database collection...")
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
    )

# 3. Chunking Logic
import re

def chunk_legal_documents(documents):
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
            
            # Approximate character index to find the current section
            snippet = " ".join(chunk_words[:10])
            char_idx = text.find(snippet)
            if char_idx == -1: char_idx = 0
            
            current_section = get_current_section(char_idx)
            
            # Prepend structural metadata
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

# 4. Main Ingestion Loop
def populate_database():
    data_dir = "../data/raw_documents"
    
    # Check if data directory exists
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Created '{data_dir}' folder. Please add PDFs and run again.")
        return

    # Find all PDFs
    pdf_files = [f for f in os.listdir(data_dir) if f.endswith('.pdf')]
    
    if not pdf_files:
        print(f"No PDFs found in the '{data_dir}' folder.")
        return

    print(f"Found {len(pdf_files)} documents to ingest. Starting process...\n")

    for filename in pdf_files:
        print(f"Processing: {filename}")
        file_path = os.path.join(data_dir, filename)
        
        try:
            # Extract Text
            doc = fitz.open(file_path)
            full_text = ""
            for page in doc:
                full_text += page.get_text() + "\n\n"
            
            doc_id = filename.replace(".pdf", "").replace(" ", "_")
            raw_doc = [{"doc_id": doc_id, "text": full_text}]
            
            # Chunk
            chunks = chunk_legal_documents(raw_doc)
            
            # Vectorize and Upsert
            current_count = client.count(collection_name=COLLECTION_NAME).count
            points = [
                PointStruct(
                    id=current_count + idx, 
                    vector=embedding_model.encode(chunk["text"]).tolist(), 
                    payload=chunk
                )
                for idx, chunk in enumerate(chunks)
            ]
            
            client.upsert(collection_name=COLLECTION_NAME, points=points)
            print(f" -> Successfully added {len(chunks)} chunks to the knowledge base.\n")
            
        except Exception as e:
            print(f" -> Failed to process {filename}: {str(e)}\n")

    print("Knowledge base construction complete! Your AI is now fully equipped.")

if __name__ == "__main__":
    populate_database()