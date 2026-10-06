"""Prompt templates and structured formatting for code repair with small local open-weight SLMs."""

import re
from typing import Optional


class PromptBuilder:
    """Constructs focused prompts optimized for code-generation SLMs (1.5B - 8B)."""

    SYSTEM_PROMPT = """You are PatchPilot, an expert automated code repair system.
Your job is to fix failing tests with the absolute minimal surgical change necessary.

RULES:
1. Analyze the stack trace and the provided file contents carefully.
2. Output the COMPLETE file content with the fix applied, preserving all existing functions, imports, and docstrings.
3. Do NOT omit or remove any existing helper functions or unchanged code.
4. Format your patch inside a single markdown code block:
```python
# Full updated file content
```
5. Do NOT include placeholder comments like '... rest of code remains the same ...'."""

    @staticmethod
    def build_repair_prompt(
        file_path: str,
        file_content: str,
        test_name: str,
        error_message: str,
        stack_trace: str,
        line_number: Optional[int] = None,
        previous_attempt_error: Optional[str] = None,
    ) -> str:
        prompt = f"""### TEST FAILURE REPORT
Failing Test: {test_name}
Target File: {file_path}
{f'Approximate Line: {line_number}' if line_number else ''}

### ERROR MESSAGE:
{error_message}

### STACK TRACE:
```
{stack_trace}
```

### ORIGINAL FULL FILE CONTENT ({file_path}):
```
{file_content}
```
"""
        if previous_attempt_error:
            prompt += f"""
### NOTE ON PREVIOUS ATTEMPT:
The previous patch failed with:
```
{previous_attempt_error}
```
Please provide an improved, corrected fix.
"""

        prompt += f"""
### TASK:
Output the FULL, complete corrected file for `{file_path}` inside a codeblock. Ensure all other existing functions and imports in the file are kept intact.
"""
        return prompt

    @staticmethod
    def extract_code_block(response_text: str) -> Optional[str]:
        """Extracts the best code block from the LLM's response."""
        # Match ```lang ... ``` blocks
        matches = re.findall(r"```(?:\w+)?\n(.*?)```", response_text, re.DOTALL)
        if matches:
            # Pick the longest code block (usually the full file or diff)
            return max(matches, key=len).strip()
        
        # If no markdown backticks, return raw response if it looks like code
        if "\n" in response_text and not response_text.startswith("I cannot"):
            return response_text.strip()
        
        return None
