"""
Upload CSV Data to MongoDB
Uploads product reviews and news articles from CSV files to MongoDB,
then automatically indexes them into the RAG vector store.
"""
import sys
import os
import pandas as pd
from datetime import datetime, timezone
from pymongo import MongoClient
from pymongo.errors import BulkWriteError

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rag.rag_service import initialize_rag_engine

# MongoDB connection
MONGODB_URI = "mongodb+srv://DevanshVerma:qazxsw123@cluster0.fxr8rpr.mongodb.net/ai_project_db?retryWrites=true&w=majority&appName=Cluster0"
DATABASE_NAME = "ai_project_db"

# Paths to CSV files
REVIEWS_CSV = os.path.join(os.path.dirname(__file__), '../output/results.csv')
NEWS_CSV = os.path.join(os.path.dirname(__file__), '../output/news_results.csv')


def upload_reviews(csv_path: str) -> int:
    """
    Upload product reviews from CSV to MongoDB
    
    Args:
        csv_path: Path to reviews CSV file
    
    Returns:
        Number of reviews uploaded
    """
    print(f"\n[STATS] Reading reviews from: {csv_path}")
    
    try:
        # Read CSV
        df = pd.read_csv(csv_path)
        print(f"   Found {len(df)} reviews in CSV")
        
        # Connect to MongoDB
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=30000)
        db = client[DATABASE_NAME]
        collection = db['reviews']
        
        # Convert DataFrame to list of dicts
        reviews = []
        for _, row in df.iterrows():
            review = {
                'category': row.get('category', 'unknown'),
                'platform': row.get('platform', 'unknown'),
                'product_url': row.get('product_url', ''),
                'original_text': row.get('original_text', ''),
                'clean_text': row.get('clean_text', ''),
                'sentiment_label': row.get('sentiment_label', 'Neutral'),
                'sentiment_score': float(row.get('sentiment_score', 0.5)),
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc)
            }
            reviews.append(review)
        
        # Upload to MongoDB (upsert to avoid duplicates)
        print("   Uploading to MongoDB...")
        
        if reviews:
            try:
                # Delete old data to avoid duplicates
                result = collection.delete_many({})
                print(f"   Cleared {result.deleted_count} old reviews")
                
                # Insert new data
                result = collection.insert_many(reviews, ordered=False)
                uploaded_count = len(result.inserted_ids)
                print(f"   [OK] Uploaded {uploaded_count} reviews to MongoDB")
                
            except BulkWriteError as e:
                uploaded_count = len(e.details.get('nInserted', 0))
                print(f"   [WARN]  Uploaded {uploaded_count} reviews (some duplicates skipped)")
        else:
            uploaded_count = 0
            print("   [WARN]  No reviews to upload")
        
        client.close()
        return uploaded_count
        
    except FileNotFoundError:
        print(f"   [FAIL] CSV file not found: {csv_path}")
        return 0
    except Exception as e:
        print(f"   [FAIL] Error uploading reviews: {str(e)}")
        return 0


def upload_news(csv_path: str) -> int:
    """
    Upload news articles from CSV to MongoDB
    
    Args:
        csv_path: Path to news CSV file
    
    Returns:
        Number of news articles uploaded
    """
    print(f"\n Reading news from: {csv_path}")
    
    try:
        # Read CSV
        df = pd.read_csv(csv_path)
        print(f"   Found {len(df)} news articles in CSV")
        
        # Connect to MongoDB
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=30000)
        db = client[DATABASE_NAME]
        collection = db['news']
        
        # Convert DataFrame to list of dicts
        news_articles = []
        for _, row in df.iterrows():
            article = {
                'platform': row.get('platform', 'unknown'),
                'keyword': row.get('keyword', ''),
                'title': row.get('title', ''),
                'description': row.get('description', ''),
                'sentiment_label': row.get('sentiment_label', 'Neutral'),
                'sentiment_score': float(row.get('sentiment_score', 0.5)),
                'published_date': row.get('published_date', str(datetime.now(timezone.utc))),
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc)
            }
            news_articles.append(article)
        
        # Upload to MongoDB (upsert to avoid duplicates)
        print("   Uploading to MongoDB...")
        
        if news_articles:
            try:
                # Delete old data to avoid duplicates
                result = collection.delete_many({})
                print(f"   Cleared {result.deleted_count} old news articles")
                
                # Insert new data
                result = collection.insert_many(news_articles, ordered=False)
                uploaded_count = len(result.inserted_ids)
                print(f"   [OK] Uploaded {uploaded_count} news articles to MongoDB")
                
            except BulkWriteError as e:
                uploaded_count = len(e.details.get('nInserted', 0))
                print(f"   [WARN]  Uploaded {uploaded_count} news articles (some duplicates skipped)")
        else:
            uploaded_count = 0
            print("   [WARN]  No news articles to upload")
        
        client.close()
        return uploaded_count
        
    except FileNotFoundError:
        print(f"   [FAIL] CSV file not found: {csv_path}")
        return 0
    except Exception as e:
        print(f"   [FAIL] Error uploading news: {str(e)}")
        return 0


def index_to_rag():
    """Index uploaded data into RAG vector store"""
    print("\n Indexing data into RAG vector store...")
    
    try:
        # Initialize RAG engine
        rag_engine = initialize_rag_engine()
        
        # Connect to MongoDB
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=30000)
        db = client[DATABASE_NAME]
        
        # Index reviews
        print("   Processing reviews...")
        reviews = list(db['reviews'].find().limit(100))  # Limit for initial indexing
        if reviews:
            chunks = rag_engine.document_processor.process_batch_from_mongodb(reviews, "review")
            result = rag_engine.index_documents(chunks)
            if result.get('success'):
                print(f"   [OK] Indexed {result.get('indexed_count', 0)} review chunks")
            else:
                print(f"   [WARN]  Error indexing reviews: {result.get('error', 'Unknown error')}")
        else:
            print("   [WARN]  No reviews found in database")
        
        # Index news
        print("   Processing news articles...")
        news = list(db['news'].find().limit(50))  # Limit for initial indexing
        if news:
            chunks = rag_engine.document_processor.process_batch_from_mongodb(news, "news")
            result = rag_engine.index_documents(chunks)
            if result.get('success'):
                print(f"   [OK] Indexed {result.get('indexed_count', 0)} news chunks")
            else:
                print(f"   [WARN]  Error indexing news: {result.get('error', 'Unknown error')}")
        else:
            print("   [WARN]  No news articles found in database")
        
        # Save vector store
        rag_engine.vector_store_manager.persist()
        print("   [OK] Vector store saved to disk")
        
        client.close()
        
    except Exception as e:
        print(f"   [FAIL] Error indexing to RAG: {str(e)}")


def main():
    """Main execution function"""
    print("=" * 60)
    print("CSV Data Upload & RAG Indexing")
    print("=" * 60)
    
    # Upload reviews
    reviews_count = upload_reviews(REVIEWS_CSV)
    
    # Upload news
    news_count = upload_news(NEWS_CSV)
    
    # Summary
    print("\n" + "=" * 60)
    print("[STATS] Upload Summary")
    print("=" * 60)
    print(f"   Reviews uploaded:       {reviews_count}")
    print(f"   News articles uploaded: {news_count}")
    print(f"   Total documents:        {reviews_count + news_count}")
    
    if reviews_count > 0 or news_count > 0:
        # Index to RAG
        index_to_rag()
        
        print("\n" + "=" * 60)
        print("[OK] Upload & Indexing Complete!")
        print("=" * 60)
        print("\n Next Steps:")
        print("   1. Start server: python server.py")
        print("   2. Test RAG queries: python scripts/test_rag.py")
        print("   3. Access API: http://localhost:8000/docs")
    else:
        print("\n[FAIL] No data uploaded. Check CSV files.")


if __name__ == "__main__":
    main()
