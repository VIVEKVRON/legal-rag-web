from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch
from backend.config import RERANKER_MODEL_ID, DEVICE

class RerankerService:
    def __init__(self):
        print("Loading Cross-Encoder Reranker...")
        self.tokenizer = AutoTokenizer.from_pretrained(RERANKER_MODEL_ID)
        self.model = AutoModelForSequenceClassification.from_pretrained(RERANKER_MODEL_ID, device_map=DEVICE)
        self.model.eval()

    def rerank(self, query: str, candidates: list, limit: int = 6):
        if not candidates:
            return []
            
        pairs = [[query, res.payload['text']] for res in candidates]
        with torch.no_grad():
            inputs = self.tokenizer(pairs, padding=True, truncation=True, max_length=512, return_tensors="pt").to(DEVICE)
            scores = self.model(**inputs).logits.view(-1).float().cpu().numpy().tolist()
            
        reranked = sorted(list(zip(candidates, scores)), key=lambda x: x[1], reverse=True)[:limit]
        return reranked
