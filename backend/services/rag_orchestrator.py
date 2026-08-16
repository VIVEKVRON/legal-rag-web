from backend.services.vector_store import VectorStoreService
from backend.services.bm25_search import BM25SearchService
from backend.services.hybrid_fusion import HybridFusionService
from backend.services.reranker import RerankerService
from backend.services.embeddings import EmbeddingService
from backend.services.llm_generator import LLMGeneratorService

def is_standard_english(text: str) -> bool:
    try:
        text.encode('ascii')
        return True
    except UnicodeEncodeError:
        return False

class RAGOrchestrator:
    def __init__(self):
        self.vector_store = VectorStoreService()
        self.bm25_search = BM25SearchService()
        self.embeddings = EmbeddingService()
        self.reranker = RerankerService()
        self.llm = LLMGeneratorService()
        self.fusion = HybridFusionService()
        
    def initialize_indexes(self):
        print("Fetching payloads to build BM25 Index...")
        payloads = self.vector_store.fetch_all_payloads()
        self.bm25_search.build_index(payloads)

    def process_query(self, query: str):
        print("Processing query...")
        query_vector = self.embeddings.encode(query)
        
        dense_results = self.vector_store.query_dense(query_vector, limit=20)
        
        if is_standard_english(query):
            sparse_results = self.bm25_search.query_sparse(query, limit=20)
        else:
            sparse_results = []
            
        if not dense_results and not sparse_results:
            return {"answer": "No relevant statutory provisions were found in the database for your query.", "sources": []}
            
        initial_results = self.fusion.reciprocal_rank_fusion(dense_results, sparse_results, limit=20)
        
        reranked_results = self.reranker.rerank(query, initial_results, limit=6)
        
        answer = self.llm.generate_answer(query, reranked_results)
        
        sources = [{"doc_id": str(res[0].payload.get("doc_id", "Unknown")), "text": str(res[0].payload.get("text", "")), "score": float(res[1])} for res in reranked_results]
        return {"answer": answer, "sources": sources}
