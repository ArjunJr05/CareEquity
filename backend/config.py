"""
Configuration module for health risk prediction pipeline.
Loads environment variables and provides centralized config.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Neo4j Configuration
    neo4j_uri: str = "neo4j://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "password"
    
    # LLM Configuration
    groq_api_key: str = "demo_mode"
    openai_api_key: str = "demo_mode"
    openai_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "openai/gpt-oss-120b"
    llm_temperature: float = 0.3
    
    # Data Paths
    data_path: str = "./data"
    neo4j_data_path: str = "./data/neo4j_data"
    sdoh_data_path: str = "./data/SDOH/modeling_dataset_with_sdoh (1).csv"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
