"""
Quick test to verify database connection with correct collection names
"""
from pymongo import MongoClient

MONGODB_URI = "mongodb+srv://DevanshVerma:qazxsw123@cluster0.fxr8rpr.mongodb.net/ai_project_db?retryWrites=true&w=majority&appName=Cluster0"

try:
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    db = client["ai_project_db"]
    
    print("[OK] MongoDB Connection successful")
    print(f"[OK] Reviews collection: {db['reviews'].count_documents({})} documents")
    print(f"[OK] News collection: {db['news'].count_documents({})} documents")
    print(f"[OK] Users collection: {db['users'].count_documents({})} documents")
    print("\n[OK] Database is working correctly!")
    
    client.close()
except Exception as e:
    print(f"[FAIL] Error: {e}")
