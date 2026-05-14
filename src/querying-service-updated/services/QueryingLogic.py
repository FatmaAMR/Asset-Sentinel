# Legacy implementation removed.
# QueryingLogic now delegates to LLMClient (see below).







import logging
from utils.llm_client import LLMClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryingLogic:
    def __init__(self):
        self.llm = LLMClient()

    async def get_llm_response(self, system_instruction: str, user_input: str) -> str | None:
        """
        Send a natural-language question to master-llm-service and get back
        a raw SQL string.

        Maps the old (system_instruction, user_input) contract onto LLMClient:
          - system_instruction  → system_prompt
          - user_input          → prompt
          - caller              → "querying"
          - temperature         → 0.1  (deterministic SQL generation)
        """
        logger.info("[QueryingLogic] Sending request to master-llm-service /generate")
        logger.debug("[QueryingLogic] user_input: %s...", user_input[:80])

        try:
            sql = await self.llm.generate(
                prompt=user_input,
                caller="querying",
                system_prompt=system_instruction,
                temperature=0.1,
                max_tokens=512,
            )
            logger.info("[QueryingLogic] SQL received: %s...", sql[:80])
            return sql

        except Exception as e:
            logger.error("[QueryingLogic] LLM call failed: %s", e)
            return None