from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Application configuration settings"""    

    # LLM Provider Settings (OpenAI-Compatible)
    llm_api_key: str  
    llm_base_url: str = "https://api.openai.com/v1"  # Default to OpenAI
    llm_model_name: str = "gpt-4o-mini"  
    llm_max_tokens: int = 500
    llm_temperature: float = 0.7
    
    # Embedding Provider Settings (OpenAI-Compatible) 
    embedding_api_key: str 
    embedding_base_url: str = "https://api.openai.com/v1"  
    embedding_model_name: str = "text-embedding-3-small"  
    embedding_dimensions: int = 1536  # Default for text-embedding-3-small
    
    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # MongoDB
    mongodb_url: str 
    database_name: str = "twerlo_db"
    
    # Qdrant
    qdrant_url: str  
    qdrant_collection_name: str = "documents"
    
    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    max_file_size_mb: int = 10
    
    class Config:
        env_file = ".env"

settings = Settings()
