import os
from qdrant_client import QdrantClient
from backend.config import COLLECTION_NAME

class VectorStoreService:
    def __init__(self):
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vector_db")
        self.client = QdrantClient(path=db_path)
        
    def query_dense(self, query_vector: list, limit: int = 20):
        try:
            return self.client.search(
                collection_name=COLLECTION_NAME, 
                query_vector=query_vector, 
                limit=limit
            )
        except Exception as e:
            print(f"Dense search error: {e}")
            return []
            
    def fetch_all_payloads(self):
        payloads = []
        try:
            scroll_results, next_page = self.client.scroll(
                collection_name=COLLECTION_NAME,
                limit=10000,
                with_payload=True,
                with_vectors=False
            )
            payloads.extend(scroll_results)
            while next_page is not None:
                scroll_results, next_page = self.client.scroll(
                    collection_name=COLLECTION_NAME,
                    limit=10000,
                    offset=next_page,
                    with_payload=True,
                    with_vectors=False
                )
                payloads.extend(scroll_results)
            return payloads
        except Exception as e:
            print(f"Failed to fetch payloads from Qdrant: {e}")
            return []
