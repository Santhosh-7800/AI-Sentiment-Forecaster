"""
Quick Setup Script for RAG Implementation
Verifies installation and configuration
"""
import sys
import os

# Add parent directory to path to import rag module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_dependencies():
    """Check if RAG dependencies are installed"""
    print(" Checking RAG dependencies...\n")
    
    required_packages = {
        "langchain": "LangChain",
        "chromadb": "ChromaDB",
        "sentence_transformers": "Sentence Transformers",
        "openai": "OpenAI Client",
        "pydantic": "Pydantic",
        "pydantic_settings": "Pydantic Settings"
    }
    
    missing = []
    installed = []
    
    for package, name in required_packages.items():
        try:
            __import__(package)
            installed.append(f"[OK] {name}")
        except ImportError:
            missing.append(f"[FAIL] {name}")
    
    for pkg in installed:
        print(pkg)
    
    if missing:
        print("\n[FAIL] Missing packages:")
        for pkg in missing:
            print(f"  {pkg}")
        print("\n Install with: pip install -r rag_requirements.txt")
        return False
    
    print("\n[OK] All dependencies installed!")
    return True


def check_env_file():
    """Check if .env file exists and has required variables"""
    print("\n Checking environment configuration...\n")
    
    if not os.path.exists(".env"):
        print("[FAIL] .env file not found")
        print(" Create one: cp .env.example .env")
        print("   Then add your OPENAI_API_KEY")
        return False
    
    # Read .env file
    with open(".env", "r") as f:
        content = f.read()
    
    required_vars = {
        "LLM_PROVIDER": "LLM Provider",
        "EMBEDDING_PROVIDER": "Embedding Provider",
        "VECTOR_STORE": "Vector Store Type"
    }
    
    # Check for appropriate API key based on provider
    if "LLM_PROVIDER=openai" in content:
        required_vars["OPENAI_API_KEY"] = "OpenAI API Key (required for LLM)"
    elif "LLM_PROVIDER=groq" in content:
        required_vars["GROQ_API_KEY"] = "Groq API Key (required for LLM)"
    
    missing = []
    found = []
    
    for var, description in required_vars.items():
        if var in content and not content.split(var)[1].split("\n")[0].strip().startswith("=your_"):
            found.append(f"[OK] {description}")
        else:
            missing.append(f"[FAIL] {description} ({var})")
    
    for item in found:
        print(item)
    
    if missing:
        print("\n[WARN]  Missing or not configured:")
        for item in missing:
            print(f"  {item}")
        print("\n Update your .env file with these values")
        return False
    
    print("\n[OK] Environment configured!")
    return True


def test_rag_initialization():
    """Test RAG system initialization"""
    print("\n Testing RAG initialization...\n")
    
    try:
        from rag.rag_service import initialize_rag_engine
        
        print("Initializing RAG engine...")
        engine = initialize_rag_engine()
        
        print("\n[OK] RAG engine initialized successfully!")
        
        # Get stats
        stats = engine.get_stats()
        print(f"\n[STATS] System Info:")
        print(f"   Vector Store: {stats['config']['vector_store_type']}")
        print(f"   LLM Model: {stats['config']['llm_model']}")
        print(f"   Embedding Model: {stats['config']['embedding_model']}")
        
        return True
        
    except Exception as e:
        print(f"\n[FAIL] RAG initialization failed: {e}")
        return False


def main():
    """Run all checks"""
    print("=" * 60)
    print("RAG Setup Verification")
    print("=" * 60)
    
    # Check dependencies
    deps_ok = check_dependencies()
    
    if not deps_ok:
        print("\n[FAIL] Setup incomplete. Install dependencies first.")
        sys.exit(1)
    
    # Check environment
    env_ok = check_env_file()
    
    if not env_ok:
        print("\n[FAIL] Setup incomplete. Configure environment variables.")
        sys.exit(1)
    
    # Test initialization
    init_ok = test_rag_initialization()
    
    if not init_ok:
        print("\n[FAIL] RAG initialization failed. Check configuration.")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("[OK] RAG Setup Complete!")
    print("=" * 60)
    print("\n Next Steps:")
    print("   1. Start server: python server.py")
    print("   2. Index data: python scripts/index_data.py")
    print("   3. Test queries: python scripts/test_rag.py")
    print("   4. View docs: http://localhost:8000/docs")
    print("\n")


if __name__ == "__main__":
    main()
