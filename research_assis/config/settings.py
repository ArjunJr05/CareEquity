import os
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

# Load .env from research_assis directory first
research_env = Path(__file__).parent.parent / ".env"
load_dotenv(research_env, override=True)

# Also load from parent project root (.env) if present
parent_env = Path(__file__).parent.parent.parent / ".env"
load_dotenv(parent_env, override=False)


def _clean_env(key: str, default: str = "") -> str:
    """Retrieve environment variable and strip surrounding quotes if present."""
    val = os.getenv(key, default)
    if val:
        val = val.strip().strip('"\'')
    return val


@dataclass(frozen=True)
class Settings:
    # API Keys (Cleaned of any quotes)
    nvidia_api_key: str = _clean_env("NVIDIA_API_KEY", "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")
    groq_api_key: str = _clean_env("GROQ_API_KEY", "")
    openrouter_api_key: str = _clean_env("OPENROUTER_API_KEY", "")
    
    # Valid Model Names (Verified Working Endpoints)
    # NVIDIA NIM endpoint: https://integrate.api.nvidia.com/v1/chat/completions
    nvidia_model: str = _clean_env("NVIDIA_MODEL", "meta/llama-3.1-8b-instruct")
    
    # Groq endpoint: https://api.groq.com/openai/v1/chat/completions
    groq_model: str = _clean_env("GROQ_MODEL", "groq/compound-mini")
    
    # OpenRouter endpoint: https://openrouter.ai/api/v1/chat/completions
    openrouter_model: str = _clean_env("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")
    
    # Performance & Concurrency Settings
    request_timeout: int = int(_clean_env("REQUEST_TIMEOUT", "4"))  # Max 4 seconds per LLM call
    max_workers: int = int(_clean_env("MAX_WORKERS", "4"))          # ThreadPool size for parallel agents
    temperature: float = float(_clean_env("TEMPERATURE", "0.2"))
    max_tokens: int = int(_clean_env("MAX_TOKENS", "1024"))


settings = Settings()
