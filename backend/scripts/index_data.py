"""
Index Data Script
Indexes documents from MongoDB into RAG vector store
"""
import sys
sys.path.append('..')

from rag.rag_service import initialize_rag_engine, get_rag_engine
from rag.document_processor import DocumentProcessor
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
MONGODB_URI = "mongodb+srv://DevanshVerma:qazxsw123@cluster0.fxr8rpr.mongodb.net/ai_project_db?retryWrites=true&w=majority&appName=Cluster0"


def index_reviews(limit=100):
    """Index product reviews from MongoDB"""
    print(f" Indexing product reviews (limit: {limit})...")
    
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        db = client["ai_project_db"]
        collection = db["product_results"]
        
        # Fetch reviews
        reviews = list(collection.find().limit(limit))
        print(f"   Found {len(reviews)} reviews in database")
        
        if not reviews:
            print("   [WARN]  No reviews found. Run scraping first.")
            return 0
        
        # Process documents
        processor = DocumentProcessor()
        chunks = processor.process_batch_from_mongodb(reviews, "review")
        print(f"   Processed into {len(chunks)} chunks")
        
        return chunks
        
    except Exception as e:
        print(f"   [FAIL] Error indexing reviews: {e}")
        return []


def index_news(limit=100):
    """Index news articles from MongoDB"""
    print(f" Indexing news articles (limit: {limit})...")
    
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        db = client["ai_project_db"]
        collection = db["news_results"]
        
        # Fetch news
        news = list(collection.find().limit(limit))
        print(f"   Found {len(news)} articles in database")
        
        if not news:
            print("   [WARN]  No news found. Run scraping first.")
            return 0
        
        # Process documents
        processor = DocumentProcessor()
        chunks = processor.process_batch_from_mongodb(news, "news")
        print(f"   Processed into {len(chunks)} chunks")
        
        return chunks
        
    except Exception as e:
        print(f"   [FAIL] Error indexing news: {e}")
        return []


def main():
    """Main indexing function"""
    print("=" * 60)
    print("RAG Data Indexing")
    print("=" * 60)
    print()
    
    # Initialize RAG engine
    print("[START] Initializing RAG engine...")
    try:
        rag_engine = initialize_rag_engine()
        print("[OK] RAG engine ready\n")
    except Exception as e:
        print(f"[FAIL] Failed to initialize RAG: {e}")
        sys.exit(1)
    
    # Index reviews
    review_chunks = index_reviews(limit=100)
    
    # Index news
    news_chunks = index_news(limit=100)
    
    # Combine all chunks
    all_chunks = review_chunks + news_chunks
    
    if not all_chunks:
        print("\n[FAIL] No documents to index. Run data collection first.")
        sys.exit(1)
    
    print(f"\n[STATS] Total chunks to index: {len(all_chunks)}")
    
    # Index to vector store
    print("\n Adding documents to vector store...")
    try:
        result = rag_engine.index_documents(all_chunks)
        
        if result["success"]:
            print(f"[OK] Successfully indexed {result['indexed_count']} documents!")
            
            # Show stats
            stats = rag_engine.get_stats()
            print(f"\n[STATS] Vector Store Stats:")
            if "vector_store" in stats:
                for key, value in stats["vector_store"].items():
                    print(f"   {key}: {value}")
        else:
            print(f"[FAIL] Indexing failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"[FAIL] Error during indexing: {e}")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("[OK] Indexing Complete!")
    print("=" * 60)
    print("\n Next Steps:")
    print("   1. Test queries: python scripts/test_rag.py")
    print("   2. Use API: http://localhost:8000/docs")
    print()


if __name__ == "__main__":
    main()
