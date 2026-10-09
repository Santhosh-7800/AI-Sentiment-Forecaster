"""
RAG Configuration Module
Centralized configuration for RAG pipeline components
"""
import os
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict
from typing import Literal

class RAGConfig(BaseSettings):
    """RAG Configuration Settings"""
    
    # LLM Configuration
    LLM_PROVIDER: Literal["openai", "huggingface", "ollama", "groq"] = "groq"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"  # or "gpt-3.5-turbo" for cheaper option
    GROQ_API_KEY: str = ""  # FREE tier available!
    GROQ_MODEL: str = "llama-3.1-8b-instant"  # Fast and free
    LLM_TEMPERATURE: float = 0.2
    LLM_MAX_TOKENS: int = 500
    
    # Embeddings Configuration
    EMBEDDING_PROVIDER: Literal["openai", "huggingface"] = "huggingface"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"  # Fast and efficient
    EMBEDDING_DIMENSION: int = 384  # Dimension for all-MiniLM-L6-v2
    
    # Vector Store Configuration
    VECTOR_STORE: Literal["chromadb", "pinecone", "faiss"] = "chromadb"
    
    # ChromaDB Settings (Local - Free)
    CHROMA_PERSIST_DIR: str = "./data/chromadb"
    CHROMA_COLLECTION_NAME: str = "market_trends"
    
    # Pinecone Settings (Cloud - Requires API Key)
    PINECONE_API_KEY: str = ""
    PINECONE_ENVIRONMENT: str = "us-east-1"
    PINECONE_INDEX_NAME: str = "market-trends-index"
    
    # FAISS Settings (Local - Free)
    FAISS_INDEX_PATH: str = "./data/faiss_index"
    
    # Document Processing
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    MAX_CHUNKS_PER_DOC: int = 10
    
    # RAG Retrieval Configuration
    RETRIEVAL_TOP_K: int = 5  # Number of relevant documents to retrieve
    SIMILARITY_THRESHOLD: float = 0.7  # Minimum similarity score
    
    # Context Window
    MAX_CONTEXT_LENGTH: int = 3000  # Max tokens for context

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


# Global config instance
rag_config = RAGConfig()


def get_rag_config() -> RAGConfig:
    """Get RAG configuration instance"""
    return rag_config


# Validation
def validate_config():
    """Validate RAG configuration"""
    errors = []
    
    if rag_config.LLM_PROVIDER == "openai" and not rag_config.OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY is required when using OpenAI as LLM provider")
    
    if rag_config.VECTOR_STORE == "pinecone" and not rag_config.PINECONE_API_KEY:
        errors.append("PINECONE_API_KEY is required when using Pinecone as vector store")
    
    if errors:
        raise ValueError(f"Configuration errors:\n" + "\n".join(f"- {e}" for e in errors))
    
    return True
