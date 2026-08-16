from rank_bm25 import BM25Okapi
from typing import List

class BM25SearchService:
    def __init__(self):
        self.bm25_index = None
        self.payloads = []
        
    def build_index(self, payloads: List):
        self.payloads = payloads
        corpus = [p.payload['text'].split() for p in payloads]
        if corpus:
            self.bm25_index = BM25Okapi(corpus)
            print(f"BM25 index built with {len(corpus)} documents.")
        else:
            print("Warning: BM25 corpus is empty.")
            
    def query_sparse(self, query: str, limit: int = 20):
        if not self.bm25_index:
            return []
        tokenized_query = query.split()
        scores = self.bm25_index.get_scores(tokenized_query)
        top_n_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:limit]
        results = []
        for idx in top_n_idx:
            if scores[idx] > 0:
                results.append(self.payloads[idx])
        return results
