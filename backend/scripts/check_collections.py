"""
Check all collections in MongoDB
"""
from pymongo import MongoClient

MONGODB_URI = "mongodb+srv://DevanshVerma:qazxsw123@cluster0.fxr8rpr.mongodb.net/ai_project_db?retryWrites=true&w=majority&appName=Cluster0"
DATABASE_NAME = "ai_project_db"

def check_collections():
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=30000)
        db = client[DATABASE_NAME]
        
        print("Available collections in database:")
        collections = db.list_collection_names()
        for collection in collections:
            count = db[collection].count_documents({})
            print(f"  - {collection}: {count} documents")
        
        client.close()
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    check_collections()
