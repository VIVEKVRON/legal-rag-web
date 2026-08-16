import torch

COLLECTION_NAME = "legal_rag_collection"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

EMBEDDING_MODEL_ID = "BAAI/bge-m3"
RERANKER_MODEL_ID = "BAAI/bge-reranker-v2-m3"
LLM_MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"

SUPPORTED_LANGUAGES = {
    "en-IN": "English (India)",
    "hi-IN": "Hindi",
    "bn-IN": "Bengali",
    "mr-IN": "Marathi",
    "te-IN": "Telugu",
    "ta-IN": "Tamil",
    "gu-IN": "Gujarati",
    "ur-IN": "Urdu",
    "kn-IN": "Kannada",
    "or-IN": "Odia",
    "ml-IN": "Malayalam"
}
