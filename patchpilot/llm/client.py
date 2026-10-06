"""Local Open-Weight SLM/LLM client supporting Ollama, llama.cpp, vLLM, and OpenAI-compatible endpoints."""

import json
import os
import requests
from dataclasses import dataclass
from typing import Dict, List, Optional, Any


@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    raw_response: Dict[str, Any]


class LocalSLMClient:
    """Client for querying local open-weight SLMs without requiring external cloud API keys."""

    def __init__(
        self,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 120,
        temperature: float = 0.1,
    ):
        self.base_url = base_url or os.getenv("PATCHPILOT_LLM_URL", "http://localhost:11434")
        self.timeout = timeout
        self.temperature = temperature
        self.model = model or os.getenv("PATCHPILOT_MODEL") or self._detect_default_model()

    def _detect_default_model(self) -> str:
        """Auto-detect available local models from Ollama, preferring code-centric SLMs."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if resp.status_code == 200:
                models = [m["name"] for m in resp.json().get("models", [])]
                if not models:
                    return "qwen2.5-coder:1.5b"
                
                # Priority order for code repair
                priority = [
                    "qwen2.5-coder",
                    "deepseek-coder",
                    "codellama",
                    "starcoder2",
                    "gemma2",
                    "llama3.2",
                    "llama3",
                    "mistral",
                ]
                for p in priority:
                    for m in models:
                        if p in m.lower():
                            return m
                return models[0]
        except Exception:
            pass
        return "qwen2.5-coder:1.5b"

    def list_available_models(self) -> List[str]:
        """List all models currently installed in the local Ollama instance."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if resp.status_code == 200:
                return [m["name"] for m in resp.json().get("models", [])]
        except Exception:
            pass
        return []

    def check_health(self) -> bool:
        """Verify if the local SLM engine is reachable."""
        try:
            resp = requests.get(f"{self.base_url}/api/version", timeout=2)
            return resp.status_code == 200
        except Exception:
            # Try OpenAI compatible /v1/models
            try:
                resp = requests.get(f"{self.base_url}/v1/models", timeout=2)
                return resp.status_code == 200
            except Exception:
                return False

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Send inference request to local SLM."""
        # 1. Try Ollama native API
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                }
            }
            if system_prompt:
                payload["system"] = system_prompt

            resp = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            if resp.status_code == 200:
                data = resp.json()
                return LLMResponse(
                    content=data.get("response", ""),
                    model=self.model,
                    provider="ollama_native",
                    raw_response=data
                )
        except requests.exceptions.RequestException:
            pass

        # 2. Try OpenAI-compatible API endpoint (/v1/chat/completions)
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            v1_url = f"{self.base_url.rstrip('/')}/v1/chat/completions"
            resp = requests.post(
                v1_url,
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": self.temperature,
                },
                timeout=self.timeout
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return LLMResponse(
                    content=content,
                    model=self.model,
                    provider="openai_compatible",
                    raw_response=data
                )
        except Exception as e:
            raise RuntimeError(
                f"Failed to connect to local open-weight SLM at {self.base_url} (model: {self.model}). "
                f"Ensure Ollama or llama.cpp is running (`ollama serve`). Error: {str(e)}"
            )

        raise RuntimeError(f"Local LLM returned non-200 status code from {self.base_url}.")
