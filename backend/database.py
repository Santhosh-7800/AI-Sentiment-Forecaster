"""
Shared MongoDB connection for all backend modules.
Keeps auth and analytics endpoints on the same database target.
"""
from __future__ import annotations

import os
import warnings

# Must be set BEFORE importing pymongo/cryptography
warnings.simplefilter("ignore", DeprecationWarning)

from pymongo import MongoClient

ATLAS_URI = os.getenv(
    "MONGODB_URI",
    "mongodb+srv://DevanshVerma:qazxsw123@cluster0.fxr8rpr.mongodb.net/ai_project_db?retryWrites=true&w=majority&appName=Cluster0",
)
LOCAL_URI = os.getenv("MONGODB_LOCAL_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGODB_DB_NAME", "ai_project_db")


def create_mongo_client() -> MongoClient:
    try:
        atlas_client = MongoClient(ATLAS_URI, serverSelectionTimeoutMS=5000)
        atlas_client.server_info()
        print("[OK] MongoDB Atlas Connected Successfully")
        return atlas_client
    except Exception as atlas_error:
        print("[FAIL] MongoDB Atlas connection failed:", atlas_error)
        print("  Trying local MongoDB fallback...")
        try:
            local_client = MongoClient(LOCAL_URI, serverSelectionTimeoutMS=2000)
            local_client.server_info()
            print("[OK] Local MongoDB Connected Successfully")
            return local_client
        except Exception as local_error:
            print("[FAIL] Local MongoDB connection failed:", local_error)
            print("[WARN] Starting in degraded DB mode")
            return MongoClient(LOCAL_URI, connect=False)


client = create_mongo_client()
db = client[DB_NAME]
