from huggingface_hub import hf_hub_download
from llama_cpp import Llama

class LLMGeneratorService:
    def __init__(self):
        print("Downloading/Loading Qwen2.5-1.5B-Instruct GGUF (4-bit)...")
        model_path = hf_hub_download(
            repo_id="Qwen/Qwen2.5-1.5B-Instruct-GGUF",
            filename="qwen2.5-1.5b-instruct-q4_k_m.gguf"
        )
        self.llm = Llama(
            model_path=model_path,
            n_ctx=4096,
            n_threads=4, # Optimize for CPU
            verbose=False
        )

    def generate_answer(self, query: str, context_chunks: list):
        context_text = "\n\n".join([f"Document [{res[0].payload['doc_id']}]: {res[0].payload['text']}" for res in context_chunks])
        
        system_prompt = (
            "You are an authoritative Senior Legal AI Advisor specializing in statutory analysis and legal research.\n"
            "Your task is to provide precise, formal, and objective legal responses based strictly on the provided context.\n\n"
            "OPERATIONAL DIRECTIVES:\n"
            "1. STRICT CONTEXTUAL BOUNDS: Rely ONLY on the explicit provisions within the provided legal context. Do not extrapolate, assume external legal frameworks, or introduce outside information.\n"
            "2. MANDATORY CITATIONS: Formally identify and cite the specific Act, Section, Article, or Document name whenever referencing legal principles (e.g., 'Pursuant to Section 10 of the Rent Control Act...').\n"
            "3. PROFESSIONAL TONE & FORMATTING: Maintain an objective, analytical, and professional tone suitable for senior legal counsel. Use Markdown formatting (bolding, bullet points, headers) to clearly structure your response for readability on a web interface.\n"
            "4. INSUFFICIENT EVIDENCE: If the provided context does not contain sufficient factual or statutory basis to answer the query, explicitly state: 'The provided legal documentation does not contain sufficient statutory authority to answer this query.'"
        )
        
        prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\nContext:\n{context_text}\n\nQuestion: {query}<|im_end|>\n<|im_start|>assistant\n"
        
        response = self.llm(
            prompt,
            max_tokens=512,
            temperature=0.1,
            stop=["<|im_end|>", "<|im_start|>"]
        )
        
        answer = response["choices"][0]["text"].strip()
        return answer
