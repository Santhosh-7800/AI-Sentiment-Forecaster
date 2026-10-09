"""
Test RAG System
Simple script to test RAG queries
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rag.rag_service import initialize_rag_engine
from dotenv import load_dotenv

# Load environment
load_dotenv()


def test_query(engine, question):
    """Test a single query"""
    print(f"\n Question: {question}")
    print("-" * 60)
    
    result = engine.query(question, return_sources=True)
    
    if result.get("success"):
        print(f"[OK] Answer:\n{result['answer']}\n")
        
        if result.get("sources"):
            print(f" Sources ({result.get('source_count', 0)}):")
            for i, source in enumerate(result['sources'][:3], 1):
                print(f"\n{i}. {source['content']}")
                print(f"   Category: {source['metadata'].get('category', 'N/A')}")
                print(f"   Sentiment: {source['metadata'].get('sentiment', 'N/A')}")
    else:
        print(f"[FAIL] Error: {result.get('error', 'Unknown error')}")


def main():
    """Run test queries"""
    print("=" * 60)
    print("RAG System Testing")
    print("=" * 60)
    
    # Initialize
    print("\n[START] Initializing RAG engine...")
    try:
        engine = initialize_rag_engine()
        print("[OK] RAG engine ready")
    except Exception as e:
        print(f"[FAIL] Initialization failed: {e}")
        sys.exit(1)
    
    # Test queries
    test_queries = [
        "What are customers saying about electronics?",
        "What is the overall sentiment for products?",
        "What are the most common complaints?",
        "Which category has the best reviews?",
        "What are the trending topics in consumer feedback?"
    ]
    
    print("\n" + "=" * 60)
    print("Running Test Queries")
    print("=" * 60)
    
    for query in test_queries:
        test_query(engine, query)
        print("\n" + "=" * 60)
    
    # Get stats
    print("\n[STATS] System Stats:")
    stats = engine.get_stats()
    print(f"   Vector Store: {stats['config']['vector_store_type']}")
    print(f"   Documents Indexed: {stats['vector_store'].get('document_count', 'N/A')}")
    print(f"   LLM Model: {stats['config']['llm_model']}")
    
    print("\n[OK] Testing Complete!")


if __name__ == "__main__":
    main()
