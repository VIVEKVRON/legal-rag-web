from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from transformers import AutoModelForSequenceClassification, AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
from rank_bm25 import BM25Okapi

COLLECTION_NAME = "legal_rag_collection"
device = "cuda" if torch.cuda.is_available() else "cpu"

print(f"Loading models on {device}...")

# 1. Connect to local database
client = QdrantClient(path="./vector_db") 

# 2. Load Models
embedding_model = SentenceTransformer("BAAI/bge-m3", device=device)

reranker_tokenizer = AutoTokenizer.from_pretrained('BAAI/bge-reranker-v2-m3')
reranker_model = AutoModelForSequenceClassification.from_pretrained('BAAI/bge-reranker-v2-m3', device_map=device)
reranker_model.eval()

llm_tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct")
llm_model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct", device_map=device)
llm_pipeline = pipeline("text-generation", model=llm_model, tokenizer=llm_tokenizer, max_new_tokens=512, temperature=0.1)

# 2.5 Initialize BM25 Hybrid Search Index
print("Initializing BM25 Hybrid Search Index...")
bm25_corpus = []
bm25_payloads = []
try:
    scroll_results, next_page = client.scroll(
        collection_name=COLLECTION_NAME,
        limit=10000,
        with_payload=True,
        with_vectors=False
    )
    for point in scroll_results:
        bm25_payloads.append(point)
        bm25_corpus.append(point.payload['text'].split())
    while next_page is not None:
        scroll_results, next_page = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=10000,
            offset=next_page,
            with_payload=True,
            with_vectors=False
        )
        for point in scroll_results:
            bm25_payloads.append(point)
            bm25_corpus.append(point.payload['text'].split())
            
    bm25_index = BM25Okapi(bm25_corpus) if bm25_corpus else None
    print(f"BM25 index built with {len(bm25_corpus)} documents.")
except Exception as e:
    print(f"Warning: Could not build BM25 index (database might be empty): {e}")
    bm25_index = None

# 3. Pipeline Functions
def process_query(user_query):
    # Vector Search
    query_vector = embedding_model.encode(user_query).tolist()
    
    print("Searching global default database using Hybrid RRF...")
    
    # Retrieve top 20 candidates for dense search
    try:
        dense_results = client.query_points(
            collection_name=COLLECTION_NAME, 
            query=query_vector, 
            limit=20
        ).points
    except Exception as e:
        dense_results = []
        print(f"Dense search error: {e}")
        
    # Retrieve top 20 candidates for sparse BM25 search
    sparse_results = []
    if bm25_index:
        tokenized_query = user_query.split()
        bm25_scores = bm25_index.get_scores(tokenized_query)
        top_n_idx = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:20]
        for idx in top_n_idx:
            if bm25_scores[idx] > 0:
                sparse_results.append(bm25_payloads[idx])

    if not dense_results and not sparse_results:
        return {"answer": "No relevant statutory provisions were found in the database for your query.", "sources": []}

    # Reciprocal Rank Fusion (RRF)
    rrf_k = 60
    rrf_scores = {}
    merged_results = {}
    
    for rank, res in enumerate(dense_results):
        point_id = res.id
        rrf_scores[point_id] = rrf_scores.get(point_id, 0.0) + (1.0 / (rrf_k + rank + 1))
        merged_results[point_id] = res

    for rank, res in enumerate(sparse_results):
        point_id = res.id
        rrf_scores[point_id] = rrf_scores.get(point_id, 0.0) + (1.0 / (rrf_k + rank + 1))
        merged_results[point_id] = res

    sorted_rrf_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)[:20]
    initial_results = [merged_results[pid] for pid in sorted_rrf_ids]

    # Rerank
    pairs = [[user_query, res.payload['text']] for res in initial_results]
    with torch.no_grad():
        inputs = reranker_tokenizer(pairs, padding=True, truncation=True, max_length=512, return_tensors="pt").to(device)
        scores = reranker_model(**inputs).logits.view(-1).float().cpu().numpy()
        
    # Sort and take the top 6 highest-scoring chunks
    reranked = sorted(list(zip(initial_results, scores)), key=lambda x: x[1], reverse=True)[:6]
    
    # Generate Answer
    context_text = "\n\n".join([f"Document [{res[0].payload['doc_id']}]: {res[0].payload['text']}" for res in reranked])
    
    # --- HIGHLY PROFESSIONAL LEGAL SYSTEM PROMPT ---
    system_prompt = (
        "You are an authoritative Senior Legal AI Advisor specializing in statutory analysis and legal research.\n"
        "Your task is to provide precise, formal, and objective legal responses based strictly on the provided context.\n\n"
        "OPERATIONAL DIRECTIVES:\n"
        "1. STRICT CONTEXTUAL BOUNDS: Rely ONLY on the explicit provisions within the provided legal context. Do not extrapolate, assume external legal frameworks, or introduce outside information.\n"
        "2. MANDATORY CITATIONS: Formally identify and cite the specific Act, Section, Article, or Document name whenever referencing legal principles (e.g., 'Pursuant to Section 10 of the Rent Control Act...').\n"
        "3. PROFESSIONAL TONE & FORMATTING: Maintain an objective, analytical, and professional tone suitable for senior legal counsel. Use Markdown formatting (bolding, bullet points, headers) to clearly structure your response for readability on a web interface.\n"
        "4. INSUFFICIENT EVIDENCE: If the provided context does not contain sufficient factual or statutory basis to answer the query, explicitly state: 'The provided legal documentation does not contain sufficient statutory authority to answer this query.'"
    )
    
    messages = [
        {"role": "system", "content": system_prompt}, 
        {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {user_query}"}
    ]
    
    prompt = llm_tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    answer = llm_pipeline(prompt)[0]["generated_text"].split("<|im_start|>assistant\n")[-1].strip()
    
    sources = [{"doc_id": res[0].payload["doc_id"], "text": res[0].payload["text"], "score": float(res[1])} for res in reranked]
    return {"answer": answer, "sources": sources}