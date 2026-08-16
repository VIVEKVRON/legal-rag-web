from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from backend.config import LLM_MODEL_ID, DEVICE

class LLMGeneratorService:
    def __init__(self):
        print("Loading Qwen2.5-1.5B-Instruct LLM...")
        self.tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL_ID)
        self.model = AutoModelForCausalLM.from_pretrained(LLM_MODEL_ID, device_map=DEVICE)
        self.pipeline = pipeline("text-generation", model=self.model, tokenizer=self.tokenizer, max_new_tokens=512, temperature=0.1)

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
        
        messages = [
            {"role": "system", "content": system_prompt}, 
            {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {query}"}
        ]
        
        prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        answer = self.pipeline(prompt)[0]["generated_text"].split("<|im_start|>assistant\n")[-1].strip()
        
        return answer
