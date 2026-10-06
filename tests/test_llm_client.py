from patchpilot.llm.client import LocalSLMClient
from patchpilot.llm.prompts import PromptBuilder

def test_prompt_builder_extract_code_block():
    text_with_block = """Here is the fix:
```python
def add(a, b):
    return a + b
```
Hope that works!"""
    extracted = PromptBuilder.extract_code_block(text_with_block)
    assert extracted == "def add(a, b):\n    return a + b"

def test_prompt_builder_repair_prompt():
    prompt = PromptBuilder.build_repair_prompt(
        file_path="src/main.py",
        file_content="def hello(): pass",
        test_name="test_hello",
        error_message="AssertionError",
        stack_trace="Traceback...",
    )
    assert "src/main.py" in prompt
    assert "test_hello" in prompt
    assert "AssertionError" in prompt

def test_local_slm_client_defaults():
    client = LocalSLMClient()
    assert client.base_url.startswith("http")
    assert client.model is not None
