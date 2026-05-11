"""
Tests for GeneralLLMService  (llama_engine.py)
 
Run all:
    pytest test_llama_engine.py -v
 
Run only unit tests (no model needed):
    pytest test_llama_engine.py -v -m unit
 
Run only integration tests (model must be loaded):
    pytest test_llama_engine.py -v -m integration
"""
 
import pytest
from unittest.mock import MagicMock, patch
 
from llama_engine import (
    GeneralLLMService,
    LLMRequest,
    LLMResponse,
    TaskType,
    BranchingLogic,
    LlamaEngine,
)
 
 
# ══════════════════════════════════════════════════════════════
#  UNIT TESTS  (mock LlamaEngine — no model file needed)
# ══════════════════════════════════════════════════════════════
 
@pytest.fixture
def mock_engine():
    """Replace LlamaEngine with a mock that returns a fixed string."""
    engine = MagicMock(spec=LlamaEngine)
    engine.generate_response.return_value = "MOCKED_OUTPUT"
    return engine
 
 
@pytest.fixture
def router():
    return BranchingLogic()
 
 
# ── Branching Logic ────────────────────────────────────────────
 
class TestBranchingLogic:
 
    @pytest.mark.unit
    def test_consulting_route_calls_engine(self, router, mock_engine):
        """BranchingLogic sends consulting payload to the engine."""
        request = LLMRequest(task_type=TaskType.CONSULTING, payload="Fan error log at 14:32")
        response = router.route(mock_engine, request)
 
        mock_engine.generate_response.assert_called_once()
        assert response.task_type == TaskType.CONSULTING
 
    @pytest.mark.unit
    def test_querying_route_calls_engine(self, router, mock_engine):
        """BranchingLogic sends querying payload to the engine."""
        request = LLMRequest(task_type=TaskType.QUERYING, payload="List machines above 80°C last week")
        response = router.route(mock_engine, request)
 
        mock_engine.generate_response.assert_called_once()
        assert response.task_type == TaskType.QUERYING
 
    @pytest.mark.unit
    def test_consulting_uses_consulting_system_prompt(self, router, mock_engine):
        """Consulting path must use the consulting system instruction."""
        request = LLMRequest(task_type=TaskType.CONSULTING, payload="some logs")
        response = router.route(mock_engine, request)
 
        call_kwargs = mock_engine.generate_response.call_args
        system_used = call_kwargs.kwargs.get("system_instruction") or call_kwargs.args[0]
        assert "diagnostic" in system_used.lower() or "log" in system_used.lower()
 
    @pytest.mark.unit
    def test_querying_uses_sql_system_prompt(self, router, mock_engine):
        """Querying path must use the SQL generation system instruction."""
        request = LLMRequest(task_type=TaskType.QUERYING, payload="some question")
        response = router.route(mock_engine, request)
 
        call_kwargs = mock_engine.generate_response.call_args
        system_used = call_kwargs.kwargs.get("system_instruction") or call_kwargs.args[0]
        assert "sql" in system_used.lower()
 
    @pytest.mark.unit
    def test_response_contains_engine_output(self, router, mock_engine):
        """LLMResponse.result must match what the engine returned."""
        request = LLMRequest(task_type=TaskType.QUERYING, payload="anything")
        response = router.route(mock_engine, request)
        assert response.result == "MOCKED_OUTPUT"
 
    @pytest.mark.unit
    def test_unknown_task_type_raises(self, router, mock_engine):
        """An unknown task_type must raise ValueError, not silently fail."""
        request = LLMRequest.__new__(LLMRequest)
        request.task_type = "invalid_type"
        request.payload = "x"
        request.max_tokens = 512
        request.temperature = 0.2
        with pytest.raises((ValueError, KeyError)):
            router.route(mock_engine, request)
 
    @pytest.mark.unit
    def test_consulting_response_has_raw_prompt(self, router, mock_engine):
        """Response must expose the system prompt used (for tracing/debugging)."""
        request = LLMRequest(task_type=TaskType.CONSULTING, payload="logs")
        response = router.route(mock_engine, request)
        assert isinstance(response.raw_prompt_used, str)
        assert len(response.raw_prompt_used) > 0
 
    @pytest.mark.unit
    def test_custom_max_tokens_passed_through(self, router, mock_engine):
        """max_tokens in LLMRequest must reach the engine."""
        request = LLMRequest(task_type=TaskType.QUERYING, payload="q", max_tokens=128)
        router.route(mock_engine, request)
 
        call_kwargs = mock_engine.generate_response.call_args
        tokens_used = call_kwargs.kwargs.get("max_tokens") or call_kwargs.args[2]
        assert tokens_used == 128
 
    @pytest.mark.unit
    def test_custom_temperature_passed_through(self, router, mock_engine):
        """temperature in LLMRequest must reach the engine."""
        request = LLMRequest(task_type=TaskType.QUERYING, payload="q", temperature=0.9)
        router.route(mock_engine, request)
 
        call_kwargs = mock_engine.generate_response.call_args
        temp_used = call_kwargs.kwargs.get("temp") or call_kwargs.args[3]
        assert temp_used == 0.9
 
 
# ── GeneralLLMService (API layer) ─────────────────────────────
 
class TestGeneralLLMServiceWithMock:
 
    @pytest.fixture
    def service_with_mock(self):
        """Patch LlamaEngine so no model file is needed."""
        with patch("llama_engine.LlamaEngine") as MockEngine:
            instance = MockEngine.return_value
            instance.generate_response.return_value = "MOCKED_OUTPUT"
            svc = GeneralLLMService()
            yield svc
 
    @pytest.mark.unit
    def test_process_consulting_returns_llm_response(self, service_with_mock):
        req = LLMRequest(task_type=TaskType.CONSULTING, payload="Fan fault log")
        resp = service_with_mock.process(req)
        assert isinstance(resp, LLMResponse)
        assert resp.task_type == TaskType.CONSULTING
 
    @pytest.mark.unit
    def test_process_querying_returns_llm_response(self, service_with_mock):
        req = LLMRequest(task_type=TaskType.QUERYING, payload="Show over-temp machines")
        resp = service_with_mock.process(req)
        assert isinstance(resp, LLMResponse)
        assert resp.task_type == TaskType.QUERYING
 
    @pytest.mark.unit
    def test_process_result_is_non_empty_string(self, service_with_mock):
        req = LLMRequest(task_type=TaskType.QUERYING, payload="anything")
        resp = service_with_mock.process(req)
        assert isinstance(resp.result, str)
        assert len(resp.result) > 0
 
 
# ══════════════════════════════════════════════════════════════
#  INTEGRATION TESTS  (real model — needs .gguf loaded)
# ══════════════════════════════════════════════════════════════
 
@pytest.mark.integration
class TestIntegrationWithRealModel:
    """
    These tests load the actual Llama model from config.settings.MODEL_PATH.
    Skip them if the model is not available:
        pytest test_llama_engine.py -v -m "not integration"
    """
 
    @pytest.fixture(scope="class")
    def service(self):
        """One service instance shared across all integration tests."""
        return GeneralLLMService()
 
    # ── Consulting path ───────────────────────────────────────
 
    def test_consulting_returns_non_empty_context(self, service):
        """Model must return something for a realistic fault log."""
        req = LLMRequest(
            task_type=TaskType.CONSULTING,
            payload=(
                "ERROR 0x4F: Hydraulic pressure sensor on Unit-7 dropped below threshold "
                "at 14:32 UTC. Temperature reading: 87°C (limit 75°C). "
                "Fan speed: 0 RPM. Last maintenance: 45 days ago."
            ),
            max_tokens=256,
            temperature=0.2,
        )
        resp = service.process(req)
 
        assert resp.task_type == TaskType.CONSULTING
        assert isinstance(resp.result, str)
        assert len(resp.result.strip()) > 10, "Response is too short — model may have failed"
 
    def test_consulting_output_is_relevant(self, service):
        """Model output should reference fault-related concepts."""
        req = LLMRequest(
            task_type=TaskType.CONSULTING,
            payload="Bearing vibration anomaly on CNC-3. Frequency spike at 120Hz since 08:00.",
            max_tokens=200,
            temperature=0.1,
        )
        resp = service.process(req)
 
        result_lower = resp.result.lower()
        # At least one diagnostic keyword should appear
        diagnostic_keywords = ["bearing", "vibration", "fault", "anomaly", "sensor",
                                "maintenance", "frequency", "failure", "check", "inspect"]
        matched = [kw for kw in diagnostic_keywords if kw in result_lower]
        assert matched, (
            f"No diagnostic keyword found in response.\nResponse: {resp.result}"
        )
 
    # ── Querying path ─────────────────────────────────────────
 
    def test_querying_returns_sql(self, service):
        """Model must return a string that looks like a SQL query."""
        req = LLMRequest(
            task_type=TaskType.QUERYING,
            payload="Show all machines where temperature exceeded 80 degrees in the last 7 days.",
            max_tokens=150,
            temperature=0.1,
        )
        resp = service.process(req)
 
        assert resp.task_type == TaskType.QUERYING
        result_upper = resp.result.upper()
        assert "SELECT" in result_upper, (
            f"Expected SQL SELECT statement.\nResponse: {resp.result}"
        )
 
    def test_querying_sql_has_where_clause(self, service):
        """Filtered question should produce SQL with a WHERE clause."""
        req = LLMRequest(
            task_type=TaskType.QUERYING,
            payload="List machine IDs where status is 'critical' and region is 'north'.",
            max_tokens=150,
            temperature=0.1,
        )
        resp = service.process(req)
 
        result_upper = resp.result.upper()
        assert "WHERE" in result_upper, (
            f"Expected WHERE clause in SQL.\nResponse: {resp.result}"
        )
 
    def test_querying_no_markdown_fences(self, service):
        """SQL output must be raw — no ```sql fences from the model."""
        req = LLMRequest(
            task_type=TaskType.QUERYING,
            payload="Get the count of alerts per machine for today.",
            max_tokens=100,
            temperature=0.1,
        )
        resp = service.process(req)
 
        assert "```" not in resp.result, (
            f"Model returned markdown fences — clean the output.\nResponse: {resp.result}"
        )
 
    # ── Both paths — response shape ───────────────────────────
 
    @pytest.mark.parametrize("task,payload", [
        (TaskType.CONSULTING, "Motor overload on Press-2 at 09:15."),
        (TaskType.QUERYING,   "Find all sensors offline for more than 1 hour."),
    ])
    def test_response_shape_both_tasks(self, service, task, payload):
        """LLMResponse fields must be correct for both task types."""
        req = LLMRequest(task_type=task, payload=payload, max_tokens=100)
        resp = service.process(req)
 
        assert isinstance(resp, LLMResponse)
        assert resp.task_type == task
        assert isinstance(resp.result, str)
        assert isinstance(resp.raw_prompt_used, str)
 