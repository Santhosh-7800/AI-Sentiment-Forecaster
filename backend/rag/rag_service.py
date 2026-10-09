"""
RAG Service Initialization Module
Initializes embeddings, LLM, and RAG engine
"""
from typing import Optional
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel

from .config import rag_config, validate_config
from .query_engine import RAGQueryEngine


# Global RAG engine instance
_rag_engine: Optional[RAGQueryEngine] = None


def get_embedding_model() -> Embeddings:
    """Get embeddings model based on configuration"""
    
    if rag_config.EMBEDDING_PROVIDER == "openai":
        from langchain_openai import OpenAIEmbeddings
        
        if not rag_config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured")
        
        return OpenAIEmbeddings(
            openai_api_key=rag_config.OPENAI_API_KEY,
            model=rag_config.EMBEDDING_MODEL
        )
    
    elif rag_config.EMBEDDING_PROVIDER == "huggingface":
        from langchain_huggingface import HuggingFaceEmbeddings
        
        return HuggingFaceEmbeddings(
            model_name=rag_config.EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},  # Change to 'cuda' if GPU available
            encode_kwargs={'normalize_embeddings': True}
        )
    
    else:
        raise ValueError(f"Unsupported embedding provider: {rag_config.EMBEDDING_PROVIDER}")


def get_llm_model() -> BaseChatModel:
    """Get LLM model based on configuration"""
    
    if rag_config.LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI
        
        if not rag_config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured")
        
        return ChatOpenAI(
            openai_api_key=rag_config.OPENAI_API_KEY,
            model_name=rag_config.OPENAI_MODEL,
            temperature=rag_config.LLM_TEMPERATURE,
            max_tokens=rag_config.LLM_MAX_TOKENS
        )
    
    elif rag_config.LLM_PROVIDER == "huggingface":
        from langchain_community.chat_models import ChatHuggingFace
        from langchain_huggingface import HuggingFaceEndpoint
        
        llm = HuggingFaceEndpoint(
            repo_id="google/flan-t5-large",
            temperature=rag_config.LLM_TEMPERATURE
        )
        return ChatHuggingFace(llm=llm)
    
    elif rag_config.LLM_PROVIDER == "ollama":
        from langchain_community.chat_models import ChatOllama
        
        return ChatOllama(
            model="llama2",
            temperature=rag_config.LLM_TEMPERATURE
        )
    
    elif rag_config.LLM_PROVIDER == "groq":
        from langchain_groq import ChatGroq
        
        if not rag_config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not configured")

        return ChatGroq(
            groq_api_key=rag_config.GROQ_API_KEY,
            model_name=rag_config.GROQ_MODEL,
            temperature=rag_config.LLM_TEMPERATURE,
            max_tokens=rag_config.LLM_MAX_TOKENS
        )
    
    else:
        raise ValueError(f"Unsupported LLM provider: {rag_config.LLM_PROVIDER}")


def initialize_rag_engine() -> RAGQueryEngine:
    """
    Initialize the RAG engine
    
    Returns:
        RAGQueryEngine instance
    """
    global _rag_engine
    
    if _rag_engine is not None:
        return _rag_engine
    
    try:
        # Validate configuration
        validate_config()
        
        print("[START] Initializing RAG Engine...")
        
        # Initialize embeddings
        print(f"  Loading embeddings model: {rag_config.EMBEDDING_MODEL}")
        embedding_model = get_embedding_model()
        print("  [OK] Embeddings loaded")
        
        # Initialize LLM
        print(f"  Loading LLM: {rag_config.OPENAI_MODEL}")
        llm_model = get_llm_model()
        print("  [OK] LLM loaded")
        
        # Initialize RAG engine
        print(f"  Setting up vector store: {rag_config.VECTOR_STORE}")
        _rag_engine = RAGQueryEngine(
            embedding_model=embedding_model,
            llm_model=llm_model
        )
        print("  [OK] Vector store initialized")
        
        print("[OK] RAG Engine initialized successfully!\n")
        
        return _rag_engine
        
    except Exception as e:
        print(f"[FAIL] Failed to initialize RAG Engine: {e}")
        raise


def get_rag_engine() -> Optional[RAGQueryEngine]:
    """
    Get the initialized RAG engine
    
    Returns:
        RAGQueryEngine instance or None if not initialized
    """
    global _rag_engine
    
    if _rag_engine is None:
        try:
            _rag_engine = initialize_rag_engine()
        except Exception as e:
            print(f"[WARN] RAG Engine not available: {e}")
            return None
    
    return _rag_engine


def reset_rag_engine():
    """Reset the RAG engine (useful for testing)"""
    global _rag_engine
    _rag_engine = None
