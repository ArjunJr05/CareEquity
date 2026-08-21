"""
Multi-provider LLM compatibility layer.
Redirects to LLMClient.
"""

from config.llm_client import get_llm_client, LLMClient

def get_llm(temperature: float = None, thinking_mode: str = "disabled"):
    """Get LLM client instance."""
    return get_llm_client()