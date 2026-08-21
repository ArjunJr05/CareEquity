#!/usr/bin/env python3
"""
Robust, Multi-Provider LLM Client for CareEquity SDOH Assistant.

Supports:
1. NVIDIA NIM API (Primary - high throughput Llama 3.1 8B)
2. Groq API (Fast secondary provider)
3. OpenRouter API (Free tier backup)
4. Built-in High-Quality Knowledge Base (Offline fallback, 100% reliable)
"""

import time
import logging
import requests
from typing import Optional, Dict, Any, Tuple
from config.settings import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Multi-provider LLM client with automatic failover and rate limiting."""

    def __init__(self):
        self.failed_providers = set()
        self.last_call_time = {}
        self.min_interval = 0.5  # Rapid execution
        self.provider_stats = {"nvidia": 0, "groq": 0, "openrouter": 0, "offline": 0}

    def _can_call(self, provider: str) -> bool:
        if provider in self.failed_providers:
            return False
        last = self.last_call_time.get(provider, 0)
        return (time.time() - last) >= self.min_interval

    def _call_nvidia(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 800) -> Optional[str]:
        """Call NVIDIA NIM API."""
        if not settings.nvidia_api_key or not self._can_call("nvidia"):
            return None

        try:
            url = "https://integrate.api.nvidia.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {settings.nvidia_api_key}",
                "Content-Type": "application/json"
            }
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            data = {
                "model": settings.nvidia_model,
                "messages": messages,
                "temperature": settings.temperature,
                "top_p": 0.7,
                "max_tokens": max_tokens,
                "stream": False
            }

            self.last_call_time["nvidia"] = time.time()
            resp = requests.post(url, headers=headers, json=data, timeout=settings.request_timeout)

            if resp.status_code == 200:
                result = resp.json()
                content = result["choices"][0]["message"]["content"]
                self.provider_stats["nvidia"] += 1
                return content.strip()
            elif resp.status_code in [429, 401, 403]:
                logger.warning(f"NVIDIA API status {resp.status_code}, marking provider failed for session")
                self.failed_providers.add("nvidia")
            else:
                logger.warning(f"NVIDIA API returned code {resp.status_code}")
            return None
        except Exception as e:
            logger.warning(f"NVIDIA request error: {e}")
            self.failed_providers.add("nvidia")
            return None

    def _call_groq(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 800) -> Optional[str]:
        """Call Groq API with valid model."""
        if not settings.groq_api_key or not self._can_call("groq"):
            return None

        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {settings.groq_api_key}",
                "Content-Type": "application/json"
            }
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            data = {
                "model": settings.groq_model,
                "messages": messages,
                "temperature": settings.temperature,
                "max_tokens": max_tokens,
                "stream": False
            }

            self.last_call_time["groq"] = time.time()
            resp = requests.post(url, headers=headers, json=data, timeout=settings.request_timeout)

            if resp.status_code == 200:
                result = resp.json()
                content = result["choices"][0]["message"]["content"]
                self.provider_stats["groq"] += 1
                return content.strip()
            elif resp.status_code in [429, 401, 403, 404]:
                logger.warning(f"Groq API status {resp.status_code}, marking provider failed for session")
                self.failed_providers.add("groq")
            else:
                logger.warning(f"Groq API returned code {resp.status_code}")
            return None
        except Exception as e:
            logger.warning(f"Groq request error: {e}")
            self.failed_providers.add("groq")
            return None

    def _call_openrouter(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 800) -> Optional[str]:
        """Call OpenRouter API."""
        if not settings.openrouter_api_key or not self._can_call("openrouter"):
            return None

        try:
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://careequity.health",
                "X-Title": "CareEquity SDOH"
            }
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            data = {
                "model": settings.openrouter_model,
                "messages": messages,
                "temperature": settings.temperature,
                "max_tokens": max_tokens
            }

            self.last_call_time["openrouter"] = time.time()
            resp = requests.post(url, headers=headers, json=data, timeout=settings.request_timeout)

            if resp.status_code == 200:
                result = resp.json()
                content = result["choices"][0]["message"]["content"]
                self.provider_stats["openrouter"] += 1
                return content.strip()
            elif resp.status_code in [429, 401, 403]:
                logger.warning(f"OpenRouter API status {resp.status_code}, marking provider failed for session")
                self.failed_providers.add("openrouter")
            return None
        except Exception as e:
            logger.warning(f"OpenRouter request error: {e}")
            self.failed_providers.add("openrouter")
            return None

    def generate(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 800) -> Tuple[str, str]:
        """
        Generate response with automatic provider failover.
        Priority: Groq (ultra-fast <1s) → NVIDIA → OpenRouter → Offline
        Returns: (response_text, provider_used)
        """
        # 1. Try Groq first for ultra-fast speed
        res = self._call_groq(prompt, system_prompt, max_tokens)
        if res:
            return res, f"Groq ({settings.groq_model})"

        # 2. Try NVIDIA
        res = self._call_nvidia(prompt, system_prompt, max_tokens)
        if res:
            return res, f"NVIDIA ({settings.nvidia_model})"

        # 3. Try OpenRouter
        res = self._call_openrouter(prompt, system_prompt, max_tokens)
        if res:
            return res, f"OpenRouter ({settings.openrouter_model})"

        # 4. Built-in Knowledge Base fallback
        self.provider_stats["offline"] += 1
        return "", "Offline Knowledge Base"

    def invoke(self, prompt: str) -> "LLMResponse":
        """Compatibility wrapper for langchain-like calls."""
        text, provider = self.generate(prompt)
        return LLMResponse(content=text, provider=provider)


class LLMResponse:
    def __init__(self, content: str, provider: str = "Unknown"):
        self.content = content
        self.provider = provider

    def __str__(self):
        return self.content


# Global client instance
_global_client: Optional[LLMClient] = None

def get_llm_client() -> LLMClient:
    """Get singleton LLMClient instance."""
    global _global_client
    if _global_client is None:
        _global_client = LLMClient()
    return _global_client
