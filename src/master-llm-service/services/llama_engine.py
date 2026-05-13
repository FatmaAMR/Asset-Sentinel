"""
General LLM Service — Core Local Inference Engine.
 
Architecture role:
    - Receives requests from Consulting (Diagnosis) Service
      → Input:  Detailed Logs / Description
      → Output: Retrieved context back to Consulting's Inference Layer
 
    - Receives requests from Querying Inference Service
      → Input:  Query Result (from schema mapper / formatter)
      → Output: SQL Query back to Querying Inference Service
 
Internal components (mirrors diagram):
    API            → GeneralLLMService  (public entry point)
    Llama Model    → LlamaEngine        (local inference, unchanged)
    Branching Logic → BranchingLogic    (routes to the right task handler)
"""
 
from enum import Enum
from dataclasses import dataclass
from llama_cpp import Llama
from config.settings import settings
 
 
# ──────────────────────────────────────────────
# Llama Model  (unchanged core engine)
# ──────────────────────────────────────────────
 
class LlamaEngine:
    """
    Core Local Inference Engine.
    Does not know about specific project tasks (SQL / Diagnosis).
    """
 
    def __init__(self):
        # Load the model locally — once for the whole service
        self.llm = Llama(
            model_path=settings.MODEL_PATH,
            n_ctx=2048,
            n_threads=4,
            verbose=False,
        )
 
    def generate_response(
        self,
        system_instruction: str,
        user_input: str,
        max_tokens: int = 512,
        temp: float = 0.2,
    ) -> str:
        # General instruction template
        prompt = (
            f"### Instruction:\n{system_instruction}\n\n"
            f"### Input:\n{user_input}\n\n"
            f"### Response:\n"
        )
        output = self.llm(
            prompt,
            max_tokens=max_tokens,
            temperature=temp,
            stop=["###", "\n\n"],
            echo=False,
        )
        return output["choices"][0]["text"].strip()
 
 
# ──────────────────────────────────────────────
# Branching Logic  (task type enum + request/response contracts)
# ──────────────────────────────────────────────
 
class TaskType(str, Enum):
    CONSULTING = "consulting"   # Consulting (Diagnosis) Service path
    QUERYING   = "querying"     # Querying Inference Service path
 
 
@dataclass
class LLMRequest:
    """Unified request contract accepted by the public API."""
    task_type: TaskType
    payload: str          # Raw input from the calling service
    max_tokens: int = 512
    temperature: float = 0.2
 
 
@dataclass
class LLMResponse:
    """Unified response returned by the public API."""
    task_type: TaskType
    result: str           # Output to be forwarded to the calling service
    raw_prompt_used: str  # Useful for debugging / tracing
 
 
class BranchingLogic:
    """
    Routes an LLMRequest to the correct task handler and returns an LLMResponse.
 
    Consulting path:
        Input  → Detailed Logs / Description (from Inference Layer)
        Output → Retrieved context  (sent back to RAG Engine / Inference Layer)
 
    Querying path:
        Input  → Query Result / natural-language question (from schema mapper)
        Output → SQL Query  (sent to Query Validator → Result Formatter)
    """
 
    # ── Consulting handler ──────────────────────────────────────────────────
 
    CONSULTING_SYSTEM = (
        "You are a diagnostic assistant for industrial equipment. "
        "You receive detailed logs and fault descriptions. "
        "Your job is to analyse the logs, identify the root cause, "
        "and return a concise contextual summary that can be used by a RAG engine "
        "to retrieve the most relevant repair procedures and historical cases. "
        "Be precise. Do not hallucinate component names or error codes."
    )
 
    def _handle_consulting(self, engine: LlamaEngine, request: LLMRequest) -> LLMResponse:
        """
        Consulting (Diagnosis) Service path.
        Payload  : detailed logs / fault description
        Returns  : contextual retrieval summary → forwarded to Inference Layer
        """
        result = engine.generate_response(
            system_instruction=self.CONSULTING_SYSTEM,
            user_input=request.payload,
            max_tokens=request.max_tokens,
            temp=request.temperature,
        )
        return LLMResponse(
            task_type=TaskType.CONSULTING,
            result=result,
            raw_prompt_used=self.CONSULTING_SYSTEM,
        )
 
    # ── Querying handler ────────────────────────────────────────────────────
 
    QUERYING_SYSTEM = (
        "You are a SQL generation assistant. "
        "You receive a natural-language question or a structured query result description. "
        "Your job is to produce a single, valid SQL query that answers the question. "
        "Output ONLY the raw SQL statement — no explanation, no markdown fences, no comments. "
        "Use standard ANSI SQL unless a dialect is specified in the input."
    )
 
    def _handle_querying(self, engine: LlamaEngine, request: LLMRequest) -> LLMResponse:
        """
        Querying Inference Service path.
        Payload  : natural-language question or query-result description
        Returns  : SQL query → forwarded to Query Validator (Security) → Result Formatter
        """
        result = engine.generate_response(
            system_instruction=self.QUERYING_SYSTEM,
            user_input=request.payload,
            max_tokens=request.max_tokens,
            temp=request.temperature,
        )
        return LLMResponse(
            task_type=TaskType.QUERYING,
            result=result,
            raw_prompt_used=self.QUERYING_SYSTEM,
        )
 
    # ── Router ──────────────────────────────────────────────────────────────
 
    def route(self, engine: LlamaEngine, request: LLMRequest) -> LLMResponse:
        """Dispatch to the correct handler based on task_type."""
        if request.task_type == TaskType.CONSULTING:
            return self._handle_consulting(engine, request)
        elif request.task_type == TaskType.QUERYING:
            return self._handle_querying(engine, request)
        else:
            raise ValueError(f"Unknown task type: {request.task_type!r}")
 
 
# ──────────────────────────────────────────────
# API  (public entry point for the General LLM Service)
# ──────────────────────────────────────────────
 
class GeneralLLMService:
    """
    Public API of the General LLM Service.
 
    Instantiate once and call .process() from any upstream service.
 
    Usage — Consulting (Diagnosis) Service:
        service = GeneralLLMService()
        response = service.process(LLMRequest(
            task_type=TaskType.CONSULTING,
            payload="ERROR 0x4F: Hydraulic pressure sensor fault at 14:32 UTC ...",
        ))
        # response.result → retrieved context → send to RAG Engine
 
    Usage — Querying Inference Service:
        response = service.process(LLMRequest(
            task_type=TaskType.QUERYING,
            payload="Show me all machines that exceeded temperature threshold last week.",
        ))
        # response.result → SQL query → send to Query Validator
    """
 
    def __init__(self):
        self._engine  = LlamaEngine()     # Llama Model  (diagram)
        self._router  = BranchingLogic()  # Branching Logic (diagram)
 
    def process(self, request: LLMRequest) -> LLMResponse:
        """Single entry point — accepts any LLMRequest, returns an LLMResponse."""
        return self._router.route(self._engine, request)
 