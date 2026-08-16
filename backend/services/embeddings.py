from sentence_transformers import SentenceTransformer
from backend.config import EMBEDDING_MODEL_ID, DEVICE

class EmbeddingService:
    def __init__(self):
        print("Loading BAAI Dense Embedding Model...")
        self.model = SentenceTransformer(EMBEDDING_MODEL_ID, device=DEVICE)
        
    def encode(self, text: str):
        return self.model.encode(text).tolist()
