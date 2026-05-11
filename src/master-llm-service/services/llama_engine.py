"""
Core Local Inference Engine. 
Does not know about specific project tasks (SQL/Diagnosis).
"""
from llama_cpp import Llama
from config.settings import settings

class LlamaEngine:
    def __init__(self):
        # Load the model locally - once for the whole service
        self.llm = Llama(
            model_path=settings.MODEL_PATH,
            n_ctx=2048,
            n_threads=4,
            verbose=False
        )

    def generate_response(self, system_instruction: str, user_input: str, max_tokens: int, temp: float):
        # Format input using a general instruction template
        prompt = f"### Instruction:\n{system_instruction}\n\n### Input:\n{user_input}\n\n### Response:\n"
        
        output = self.llm(
            prompt,
            max_tokens=max_tokens,
            temperature=temp,
            stop=["###", "\n\n"],
            echo=False
        )
        return output["choices"][0]["text"].strip()