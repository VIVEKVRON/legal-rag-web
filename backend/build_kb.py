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
def chunk_legal_documents(documents):
    chunks = []
    for doc in documents:
        raw_chunks = [chunk.strip() for doc_chunk in doc["text"].split('\n\n') if (chunk := doc_chunk.strip())]
        if not raw_chunks:
            continue
        parent_context = raw_chunks[0] 
        for i, text_chunk in enumerate(raw_chunks):
            final_text = text_chunk if i == 0 else f"{parent_context}\n{text_chunk}"
            chunks.append({
                "chunk_id": f"{doc['doc_id']}_chunk_{i}",
                "doc_id": doc["doc_id"],
                "text": final_text 
            })
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