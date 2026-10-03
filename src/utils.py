import re
import urllib.request
import json
import os
from typing import Optional

DEFAULT_OLLAMA_MODEL = "qwen2.5-coder:1.5b"


class LLMResponse:
    def __init__(self, content: str):
        self.content = content or ""


class UnifiedLLM:
    """
    Unified LLM interface providing drop-in compatibility across:
    - Groq (Ultra-fast cloud inference, 800+ tokens/sec, generates in seconds)
    - Google Gemini (Fast cloud inference)
    - Local Ollama (Offline local inference)
    """
    def __init__(
        self,
        provider: str = "ollama",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None
    ):
        self.provider = (provider or "ollama").lower()
        self.model = model
        self.api_key = api_key or os.environ.get("GROQ_API_KEY") or os.environ.get("GEMINI_API_KEY")
        self.temperature = temperature
        self.max_tokens = max_tokens

    def invoke(self, prompt: str) -> LLMResponse:
        # 1. Groq Provider (Sub-second execution)
        if self.provider == "groq":
            try:
                from groq import Groq
                client = Groq(api_key=self.api_key)
                model_name = self.model or "llama-3.3-70b-versatile"
                resp = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens or 600,
                )
                text = resp.choices[0].message.content or ""
                return LLMResponse(text)
            except Exception as e:
                return LLMResponse(f"Groq API Error: {str(e)}")

        # 2. Gemini Provider (Fast execution)
        elif self.provider in ["gemini", "google"]:
            try:
                from google import genai
                client = genai.Client(api_key=self.api_key)
                model_name = self.model or "gemini-2.5-flash"
                resp = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                return LLMResponse(resp.text or "")
            except Exception as e:
                return LLMResponse(f"Gemini API Error: {str(e)}")

        # 3. Local Ollama Provider (Offline)
        else:
            from langchain_ollama import ChatOllama
            kwargs = {
                "model": self.model or DEFAULT_OLLAMA_MODEL,
                "temperature": self.temperature,
                "num_ctx": 512,
                "keep_alive": "1h",
            }
            if self.max_tokens is not None:
                kwargs["num_predict"] = self.max_tokens

            llm = ChatOllama(**kwargs)
            res = llm.invoke(prompt)
            return LLMResponse(res.content if hasattr(res, "content") else str(res))


def get_llm(
    model: Optional[str] = None,
    provider: str = "ollama",
    api_key: Optional[str] = None,
    temperature: float = 0.0,
    max_tokens: Optional[int] = None
) -> UnifiedLLM:
    """
    Factory function returning a unified LLM instance.
    """
    return UnifiedLLM(
        provider=provider,
        model=model,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens
    )


def extract_code(text: str) -> str:
    """
    Robustly extract Python code from Markdown code blocks or plain text.
    """
    if not text:
        return ""

    pattern = r"```(?:python|py)?\r?\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        longest_block = max(matches, key=len)
        return longest_block.strip()

    if "```" in text:
        parts = text.split("```")
        if len(parts) >= 2:
            code = parts[1]
            if code.startswith("python"):
                code = code[6:]
            elif code.startswith("py"):
                code = code[2:]
            return code.strip()

    return text.strip()


def get_available_models(host: str = "http://localhost:11434") -> list[str]:
    """
    Retrieve all installed model names from local Ollama.
    """
    try:
        req = urllib.request.Request(f"{host}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name", "") for m in data.get("models", [])]
                return [m for m in models if "embed" not in m]
    except Exception:
        pass
    return ["qwen2.5-coder:1.5b", "qwen2.5-coder:7b"]


def check_ollama_status(model: Optional[str] = None, host: str = "http://localhost:11434") -> tuple[bool, str]:
    """
    Check whether Ollama is running and whether the specified model is present.
    """
    check_model = model or DEFAULT_OLLAMA_MODEL
    try:
        req = urllib.request.Request(f"{host}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name", "") for m in data.get("models", [])]
                model_base = check_model.split(":")[0]
                model_found = any(m == check_model or m.startswith(model_base) for m in models)
                if model_found:
                    return True, "Ollama is ready."
                else:
                    return False, f"Model '{check_model}' not found. Available: {', '.join(models) if models else 'None'}."
            return False, f"Ollama HTTP {resp.status}."
    except Exception as e:
        return False, f"Cannot connect to Ollama ({str(e)})."
