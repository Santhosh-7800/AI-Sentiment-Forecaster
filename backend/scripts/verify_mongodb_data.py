"""
Verify MongoDB Data
Check what data exists in MongoDB collections
"""
from pymongo import MongoClient

MONGODB_URI = "mongodb+srv://DevanshVerma:qazxsw123@cluster0.fxr8rpr.mongodb.net/ai_project_db?retryWrites=true&w=majority&appName=Cluster0"
DATABASE_NAME = "ai_project_db"

def verify_data():
    print("=" * 60)
    print("MongoDB Data Verification")
    print("=" * 60)
    
    try:
        # Connect to MongoDB
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=30000)
        db = client[DATABASE_NAME]
        
        # Check reviews collection
        print("\n[STATS] PRODUCT REVIEWS (from results.csv)")
        print("-" * 60)
        reviews_count = db['reviews'].count_documents({})
        print(f"Total reviews: {reviews_count}")
        
        if reviews_count > 0:
            # Get sample review
            sample_review = db['reviews'].find_one()
            print(f"\n[OK] Sample Review:")
            print(f"   Category: {sample_review.get('category')}")
            print(f"   Platform: {sample_review.get('platform')}")
            print(f"   Sentiment: {sample_review.get('sentiment_label')} ({sample_review.get('sentiment_score'):.2f})")
            print(f"   Text: {sample_review.get('original_text')[:100]}...")
            
            # Get sentiment breakdown
            print(f"\n[UP] Sentiment Breakdown:")
            for sentiment in ['Positive', 'Negative', 'Neutral']:
                count = db['reviews'].count_documents({'sentiment_label': sentiment})
                print(f"   {sentiment}: {count} reviews")
            
            # Get category breakdown
            print(f"\n Category Breakdown:")
            categories = db['reviews'].distinct('category')
            for category in categories:
                count = db['reviews'].count_documents({'category': category})
                print(f"   {category}: {count} reviews")
        
        # Check news collection
        print("\n\n NEWS ARTICLES (from news_results.csv)")
        print("-" * 60)
        news_count = db['news'].count_documents({})
        print(f"Total news articles: {news_count}")
        
        if news_count > 0:
            # Get sample news
            sample_news = db['news'].find_one()
            print(f"\n[OK] Sample News Article:")
            print(f"   Platform: {sample_news.get('platform')}")
            print(f"   Keyword: {sample_news.get('keyword')}")
            print(f"   Sentiment: {sample_news.get('sentiment_label')} ({sample_news.get('sentiment_score'):.2f})")
            print(f"   Title: {sample_news.get('title')[:100]}...")
            
            # Get sentiment breakdown
            print(f"\n[UP] Sentiment Breakdown:")
            for sentiment in ['Positive', 'Negative', 'Neutral']:
                count = db['news'].count_documents({'sentiment_label': sentiment})
                print(f"   {sentiment}: {count} articles")
        
        print("\n\n" + "=" * 60)
        print("[OK] DATA VERIFICATION COMPLETE")
        print("=" * 60)
        print(f"\n[STATS] Total Documents in MongoDB: {reviews_count + news_count}")
        print(f"   - Product Reviews (Amazon data): {reviews_count}")
        print(f"   - News Articles: {news_count}")
        
        client.close()
        
    except Exception as e:
        print(f"\n[FAIL] Error: {str(e)}")

if __name__ == "__main__":
    verify_data()
