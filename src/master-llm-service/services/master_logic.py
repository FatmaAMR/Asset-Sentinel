# Main business logic to handle task switching (SQL vs. Diagnosis)

"""
High-level orchestrator that decides how to process the request 
based on the task type (e.g., Text-to-SQL vs. Technical Advice).
"""

from .llama_engine import LlamaEngine

class MasterLogic:
    def __init__(self):
        self.engine = LlamaEngine()

    async def handle_task(self, task_type: str, user_input: str):
        # Switch between different prompts based on task_type
        pass