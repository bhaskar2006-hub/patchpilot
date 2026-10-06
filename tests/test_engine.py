import os
import tempfile
from unittest.mock import MagicMock, patch
from patchpilot.engine import SelfHealingEngine
from patchpilot.llm.client import LLMResponse

def test_engine_already_passing():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a passing test
        with open(os.path.join(tmpdir, "test_pass.py"), "w") as f:
            f.write("def test_ok(): assert 1 == 1\n")

        engine = SelfHealingEngine(workspace_dir=tmpdir)
        res = engine.heal("pytest test_pass.py")
        assert res.initial_passed is True
        assert res.healed is True

@patch("patchpilot.llm.client.LocalSLMClient.generate")
def test_engine_successful_heal(mock_generate):
    mock_generate.return_value = LLMResponse(
        content="""```python
def divide(a: int, b: int) -> int:
    if b == 0:
        return 0
    return a // b
```""",
        model="qwen2.5-coder:1.5b",
        provider="mock",
        raw_response={},
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        calc_path = os.path.join(tmpdir, "calc.py")
        with open(calc_path, "w") as f:
            f.write("""def divide(a: int, b: int) -> int:
    return a // b
""")

        test_path = os.path.join(tmpdir, "test_calc.py")
        with open(test_path, "w") as f:
            f.write("""from calc import divide

def test_divide():
    assert divide(10, 0) == 0
""")

        engine = SelfHealingEngine(workspace_dir=tmpdir, max_attempts=1)
        res = engine.heal("pytest test_calc.py")

        assert res.initial_passed is False
        assert res.healed is True
        assert len(res.attempts) == 1
        assert res.attempts[0].success is True
