"""
TrendAI Backend Server
Main FastAPI application with authentication, scraping, and sentiment analysis
"""
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from oauth2 import verify_access_token
from routers import authentication
from routers.authentication import verify_password,otp_collection,generate_otp
from hashing import hash_password
from groq import Groq
from schemas import ForgotPasswordRequest,ProfileUpdateRequest,RealtimeAnalyzeRequest,ChatRequest
import sys
import pandas as pd
import time
import logging
import warnings

# Suppress cryptography deprecation warning from pymongo
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pymongo")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import scraping modules (optional)
try:
    from scraper.selenium_scraper import scrape_reviews, get_product_links
    from scraper.news_scraper import scrape_news
    SCRAPING_ENABLED = True
except ImportError as e:
    print(f"[WARN]  Scraping modules not available: {e}")
    print("  Install selenium and beautifulsoup4 to enable scraping features")
    SCRAPING_ENABLED = False

# Try to import sentiment engine (optional)
try:
    from llm.sentiment_engine import get_sentiment
    from utils.cleaner import clean_text
    SENTIMENT_ENABLED = True
except ImportError as e:
    print(f"[WARN]  Sentiment analysis not available: {e}")
    print("  Install transformers and torch to enable sentiment analysis")
    SENTIMENT_ENABLED = False

# Try to import RAG routes (optional)
try:
    from routers import rag_routes
    RAG_ENABLED = True
except ImportError as e:
    print(f"[WARN]  RAG features not available: {e}")
    print("  Install RAG dependencies: pip install -r rag_requirements.txt")
    RAG_ENABLED = False

# Try to import Product Insights routes (optional)
try:
    from routers import product_insights_routes
    INSIGHTS_ENABLED = True
except ImportError as e:
    print(f"[WARN]  Product insights features not available: {e}")
    print("  Install dependencies: pip install langchain-groq")
    INSIGHTS_ENABLED = False

# Try to import Pipeline routes (optional)
try:
    from routers import pipeline_routes
    from services.automated_pipeline import pipeline
    PIPELINE_ENABLED = True
except ImportError as e:
    print(f"[WARN]  Pipeline features not available: {e}")
    print("  Install dependencies: pip install apscheduler")
    PIPELINE_ENABLED = False

# Try to import Groq Analysis routes (optional)
try:
    from routers import groq_analysis_routes
    GROQ_ANALYSIS_ENABLED = True
except ImportError as e:
    print(f"[WARN]  Groq analysis features not available: {e}")
    print("  Install dependencies: pip install langchain-groq")
    GROQ_ANALYSIS_ENABLED = False

import os
import math
from bson import ObjectId
import random
<<<<<<< HEAD
=======
from services.realtime_analysis import RealtimeAnalyzer
>>>>>>> 4463506 (Integrated TrendBot with Groq and polished UI styling)
from datetime import datetime,timedelta
from database import client, db
from routers import reports_routes
from routers import billing_routes

# Try to import realtime analysis service (optional)
try:
    from services.realtime_analysis import RealtimeAnalyzer
    REALTIME_ENABLED = True
except ImportError as e:
    print(f"[WARN]  Realtime analysis service not available: {e}")
    REALTIME_ENABLED = False

# Try to import analytics routes (optional)
try:
    from routers import analytics_routes
    ANALYTICS_ENABLED = True
except ImportError as e:
    print(f"[WARN]  Analytics routes not available: {e}")
    ANALYTICS_ENABLED = False

# Try to import keyword routes (optional)
try:
    from routers import keyword_routes
    KEYWORD_ENABLED = True
except ImportError as e:
    print(f"[WARN]  Keyword routes not available: {e}")
    KEYWORD_ENABLED = False

print("PYTHON PATH:", sys.executable)
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
# Initialize FastAPI app
app = FastAPI(
    title="TrendAI API",
    description="AI-powered sentiment analysis and market tracking platform",
    version="1.0.0"
)

# CORS Middleware - Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication router
app.include_router(authentication.router)

# Include analytics router (new)
if ANALYTICS_ENABLED:
    app.include_router(analytics_routes.router)

# Include keyword analysis router
if KEYWORD_ENABLED:
    app.include_router(keyword_routes.router)

# Include custom reports router
app.include_router(reports_routes.router)

# Include billing router for Razorpay payments
app.include_router(billing_routes.router)

# Include RAG router if available
if RAG_ENABLED:
    app.include_router(rag_routes.router)
    print("[OK] RAG routes loaded")

# Include Product Insights router if available
if INSIGHTS_ENABLED:
    app.include_router(product_insights_routes.router)
    print("[OK] Product insights routes loaded")

# Include Pipeline router if available
if PIPELINE_ENABLED:
    app.include_router(pipeline_routes.router)
    print("[OK] Pipeline routes loaded")

# Include Groq Analysis router if available
if GROQ_ANALYSIS_ENABLED:
    app.include_router(groq_analysis_routes.router)
    print("[OK] Groq analysis routes loaded")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

product_collection = db["reviews"]
news_collection = db["news"]
realtime_collection = db["realtime_analysis"]
realtime_analyzer = RealtimeAnalyzer() if REALTIME_ENABLED else None




def _sanitize_for_json(value):
    """Convert Mongo/Pandas edge values (NaN/Inf) into JSON-safe values."""
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return 0.0
        return value
    if isinstance(value, dict):
        return {k: _sanitize_for_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize_for_json(v) for v in value]
    return value


# -----------------------
# Root Endpoint
# -----------------------
@app.get("/")
def read_root():
    return {
        "message": "Welcome to TrendAI API",
        "version": "1.0.0",
        "status": "running"
    }


# -----------------------
# Protected Route Example
# -----------------------
@app.get("/protected")
def protected_route(token: str = Depends(oauth2_scheme)):
    payload = verify_access_token(token)
    return {"message": "You are authorized", "user": payload}


# -----------------------
# Product Scraping Route
# -----------------------
@app.get("/api/scrape/products")
def run_pipeline():
    """
    Scrape product reviews from Amazon and analyze sentiment
    """
    if not SCRAPING_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="Scraping functionality is not available. Install required dependencies."
        )
    
    if not SENTIMENT_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="Sentiment analysis is not available. Install required dependencies."
        )
    
    categories = {
        "electronics": "https://www.amazon.in/s?i=electronics",
        "clothes": "https://www.amazon.in/s?i=fashion",
        "essentials": "https://www.amazon.in/s?i=grocery"
    }
   
    all_results = []

    for category_name, category_url in categories.items():
        print(f"Scraping category: {category_name}")

        product_links = get_product_links(category_url)
        product_links = product_links[:3]  # Limit to avoid blocking

        for product_url in product_links:
            try:
                raw_reviews = scrape_reviews(product_url)
                print(f"Reviews found: {len(raw_reviews)}")

                for item in raw_reviews:
                    cleaned = clean_text(item["text"])
                    sentiment = get_sentiment(cleaned)

                    data = {
                        "category": category_name,
                        "product_url": product_url,
                        "review": item["text"],
                        "sentiment_label": sentiment["label"],
                        "confidence_score": sentiment.get("confidence_score", 0),
                        "negative_percent": sentiment.get("percentages", {}).get("Negative", 0),
                        "neutral_percent": sentiment.get("percentages", {}).get("Neutral", 0),
                        "positive_percent": sentiment.get("percentages", {}).get("Positive", 0),
                    }

                    all_results.append(data)
                    product_collection.insert_one(data)

                time.sleep(5)  # Avoid rate limiting

            except Exception as e:
                print(f"Error scraping {product_url}: {e}")
                continue

    return {"message": "Product scraping completed", "count": len(all_results)}


# -----------------------
# News Scraping Route
# -----------------------
@app.get("/api/scrape/news")
def run_news_pipeline():
    """
    Scrape news articles and analyze sentiment
    """
    if not SCRAPING_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="Scraping functionality is not available. Install required dependencies."
        )
    
    if not SENTIMENT_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="Sentiment analysis is not available. Install required dependencies."
        )
    
    news_data = scrape_news()
    results = []

    for article in news_data:
        combined_text = article["title"] + " " + article["description"]
        cleaned = clean_text(combined_text)
        sentiment = get_sentiment(cleaned)

        data = {
            "platform": "news",
            "keyword": article["keyword"],
            "title": article["title"],
            "description": article["description"],
            "sentiment_label": sentiment["label"],
            "sentiment_score": sentiment.get("confidence_score", 0),
            "published_date": article["published_date"]
        }

        results.append(data)
        news_collection.insert_one(data)

    return {"message": "News scraping completed", "count": len(results)}


# -----------------------
# Get Stored Products
# -----------------------
@app.get("/api/products")
def get_products():
    """
    Retrieve all stored product reviews and sentiments
    """
    data = list(product_collection.find({}, {"_id": 0}).limit(100))
    data = _sanitize_for_json(data)
    return {"count": len(data), "data": data}


# -----------------------
# Get Stored News
# -----------------------
@app.get("/api/news")
def get_news():
    """
    Retrieve all stored news articles and sentiments
    """
    data = list(news_collection.find({}, {"_id": 0}).limit(100))
    data = _sanitize_for_json(data)
    return {"count": len(data), "data": data}


@app.post("/api/realtime/analyze")
def analyze_realtime(payload: RealtimeAnalyzeRequest, token: str = Depends(oauth2_scheme)):
    """
    Real-time product sentiment analysis with free-tier-safe API budget controls.
    """
    verify_access_token(token)

    if not REALTIME_ENABLED or realtime_analyzer is None:
        raise HTTPException(status_code=503, detail="Realtime analysis service is not available")

    try:
        logger.info(f" Received analysis request for product: {payload.product}")
        
        result = realtime_analyzer.analyze_product(
            product=payload.product,
            max_articles=payload.max_articles,
            force_refresh=payload.force_refresh,
        )
        
        logger.info(f"[OK] Analysis returned successfully for: {payload.product}")

        # Best-effort analytics logging: do not fail API response if DB write fails.
        try:
            realtime_collection.insert_one(
                {
                    "product": result.get("product"),
                    "source": result.get("source"),
                    "generated_at": result.get("generated_at"),
                    "sentiment_score": result.get("sentiment_score", 0),
                    "article_count": result.get("article_count", 0),
                    "summary": result.get("summary", ""),
                    "budget": result.get("budget", {}),
                }
            )
        except Exception as db_err:
            logger.warning(f"[WARN]  Failed to log analysis to DB: {str(db_err)}")
            pass
        return result
    except ValueError as e:
        logger.error(f"[FAIL] ValueError: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[FAIL] Analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Realtime analysis failed: {str(e)}")


@app.get("/api/realtime/budget")
def realtime_budget_status(token: str = Depends(oauth2_scheme)):
    verify_access_token(token)
    if not REALTIME_ENABLED or realtime_analyzer is None:
        raise HTTPException(status_code=503, detail="Realtime analysis service is not available")
    return realtime_analyzer.budget.status()


# -----------------------
# Health Check
# -----------------------
@app.get("/api/health")
def health_check():
    """
    Check if all services are running properly
    """
    mongo_status = "connected"
    try:
        client.server_info()
    except:
        mongo_status = "disconnected"
    
    return {
        "status": "healthy",
        "mongodb": mongo_status,
        "scraping_enabled": SCRAPING_ENABLED,
        "sentiment_enabled": SENTIMENT_ENABLED,
        "rag_enabled": RAG_ENABLED,
        "version": "1.0.0"
    }


# -----------------------
# Startup: Load CSV Data to MongoDB
# -----------------------
@app.on_event("startup")
async def load_csv_to_mongodb():
    """Load CSV data into MongoDB collections if they are empty on startup"""
    try:
        # Load product reviews from CSV
        if product_collection.count_documents({}) == 0:
            csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "results.csv")
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                records = []
                for _, row in df.iterrows():
                    records.append({
                        "category": str(row.get("category", "unknown")),
                        "platform": str(row.get("platform", "amazon")),
                        "product_url": str(row.get("product_url", "")),
                        "review": str(row.get("original_text", "")),
                        "clean_text": str(row.get("clean_text", "")),
                        "sentiment_label": str(row.get("sentiment_label", "Neutral")),
                        "confidence_score": float(row.get("sentiment_score", 0)),
                    })
                if records:
                    product_collection.insert_many(records)
                    print(f"[OK] Loaded {len(records)} product reviews from CSV to MongoDB")
            else:
                print(f"[WARN] CSV file not found at: {csv_path}")
        else:
            print(f"[OK] Products collection: {product_collection.count_documents({})} documents already loaded")

        # Load news articles from CSV
        if news_collection.count_documents({}) == 0:
            csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "news_results.csv")
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                records = df.fillna("").to_dict(orient="records")
                if records:
                    news_collection.insert_many(records)
                    print(f"[OK] Loaded {len(records)} news articles from CSV to MongoDB")
        else:
            print(f"[OK] News collection: {news_collection.count_documents({})} documents already loaded")

    except Exception as e:
        print(f"[WARN] CSV loading error: {e}")

    # Initialize automated pipeline if available
    if PIPELINE_ENABLED:
        try:
            pipeline.start()
            print("[OK] Automated pipeline scheduler started")
        except Exception as e:
            print(f"[WARN] Failed to start pipeline scheduler: {e}")


# -----------------------
# Shutdown: Stop Pipeline
# -----------------------
@app.on_event("shutdown")
async def shutdown_pipeline():
    """Stop the automated pipeline scheduler on shutdown"""
    if PIPELINE_ENABLED:
        try:
            pipeline.stop()
            print("[OK] Automated pipeline scheduler stopped")
        except Exception as e:
            print(f"[WARN] Error stopping pipeline: {e}")


# -----------------------
# System Stats Endpoint
# -----------------------
@app.get("/api/stats")
def get_system_stats():
    """Get system statistics for admin panel"""
    try:
        product_count = product_collection.count_documents({})
        news_count = news_collection.count_documents({})
        user_count = db["users"].count_documents({})

        pos = product_collection.count_documents({"sentiment_label": "Positive"})
        neg = product_collection.count_documents({"sentiment_label": "Negative"})
        neu = product_collection.count_documents({"sentiment_label": "Neutral"})
        total = product_count if product_count > 0 else 1

        if pos >= neg and pos >= neu:
            dominant = "Positive"
        elif neg >= pos and neg >= neu:
            dominant = "Negative"
        else:
            dominant = "Neutral"

        return {
            "total_reviews": product_count,
            "total_news": news_count,
            "total_users": user_count,
            "positive": pos,
            "negative": neg,
            "neutral": neu,
            "positive_pct": round((pos / total) * 100),
            "negative_pct": round((neg / total) * 100),
            "neutral_pct": round((neu / total) * 100),
            "dominant_sentiment": dominant,
            "scraping_enabled": SCRAPING_ENABLED,
            "sentiment_enabled": SENTIMENT_ENABLED,
            "rag_enabled": RAG_ENABLED,
        }
    except Exception as e:
        return {"error": str(e), "total_reviews": 0, "total_news": 0, "total_users": 0}


# -----------------------
# Current User Profile
# -----------------------
@app.get("/api/me")
def get_my_profile(token: str = Depends(oauth2_scheme)):
    """Get the currently logged-in user's profile"""
    payload = verify_access_token(token)
    user_id = payload.get("user_id")
    try:
        user = db["users"].find_one({"_id": ObjectId(user_id)}, {"_id": 0, "password": 0})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/me")
def update_my_profile(payload: ProfileUpdateRequest, token: str = Depends(oauth2_scheme)):
    """Update the currently logged-in user's basic profile fields."""
    token_payload = verify_access_token(token)
    user_id = token_payload.get("user_id")

    update_data = payload.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided to update")

    try:
        db["users"].update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
        user = db["users"].find_one({"_id": ObjectId(user_id)}, {"_id": 0, "password": 0})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": "Profile updated", "user": user}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/request-otp")
async def request_otp(payload: dict):
    email = payload.get("email")
    user = db["users"].find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    otp = generate_otp()
    # Store OTP with a 10-minute expiry
    otp_collection.update_one(
        {"email": email},
        {"$set": {"otp": otp, "expires_at": datetime.utcnow() + timedelta(minutes=10)}},
        upsert=True
    )
    
    # In a real app, use an email service (SendGrid/Mailgun) here
    print(f"DEBUG: OTP for {email} is {otp}") 
    return {"message": "OTP sent to email"}

@app.post("/api/auth/verify-reset")
async def verify_and_reset(payload: dict):
    email = payload.get("email")
    otp_code = payload.get("otp")
    new_password = payload.get("new_password")

    entry = otp_collection.find_one({"email": email, "otp": otp_code})
    if not entry or entry["expires_at"] < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    hashed = hash_password(new_password)
    db["users"].update_one({"email": email}, {"$set": {"password": hashed}})
    otp_collection.delete_one({"email": email})
    
    return {"message": "Password reset successful"}
# -----------------------
# Settings 
#-----------------------
@app.get("/api/settings")
async def get_settings(token: str = Depends(oauth2_scheme)):
    # 1. Decode the token to get the user payload
    payload = verify_access_token(token)
    user_id = payload.get("user_id")

    # 2. Use the user_id to find settings
    # Note: If using Motor (async), use await. If using standard pymongo, remove await.
    settings = db["settings"].find_one({"user_id": user_id})

    if not settings:
        return {
            "emailAlerts": True,
            "systemUpdates": True,
            "twoFactorEnabled": False,
            "plan": "Free",
            "price": "$0",
            "cardLast4": "",
            "cardExpiry": "",
            "usage": {"ai": 0, "storage": 0}
        }

    settings.pop("_id", None)
    return settings

@app.put("/api/settings")
async def update_settings(data: dict, token: str = Depends(oauth2_scheme)):
    payload = verify_access_token(token)
    user_id = payload.get("user_id")
    # Get existing settings to preserve subscription metadata
    existing_settings = db["settings"].find_one({"user_id": user_id})

    # Check if user is trying to downgrade their plan
    if existing_settings:
        current_plan = existing_settings.get("plan", "Free")
        new_plan = data.get("plan", current_plan)
        payment_status = existing_settings.get("payment_status", "none")

        # Prevent downgrades for users with active subscriptions
        if payment_status == "active" and current_plan != "Free":
            plan_tiers = {"Free": 0, "Pro Business": 1, "Enterprise": 2}
            current_tier = plan_tiers.get(current_plan, 0)
            new_tier = plan_tiers.get(new_plan, 0)

            if new_tier < current_tier:
                raise HTTPException(
                    status_code=403,
                    detail=f"Cannot downgrade from {current_plan} to {new_plan}. Users with active paid subscriptions can only upgrade."
                )

    update_doc = {
        "user_id": user_id, # Ensure user_id is linked
        "emailAlerts": data.get("emailAlerts", True),
        "systemUpdates": data.get("systemUpdates", True),
        "twoFactorEnabled": data.get("twoFactorEnabled", False),
        "plan": data.get("plan"),
        "price": data.get("price"),
        "cardLast4": data.get("cardLast4"),
        "cardExpiry": data.get("cardExpiry"),
        "usage": data.get("usage", {"ai": 0, "storage": 0})
    }


    # Preserve subscription metadata when switching between plans
    if existing_settings:
        # Keep subscription status fields when updating plan (don't overwrite on plan switches)
        if "payment_status" in existing_settings:
            update_doc["payment_status"] = existing_settings["payment_status"]
        if "plan_expiry_date" in existing_settings:
            update_doc["plan_expiry_date"] = existing_settings["plan_expiry_date"]
        if "plan_purchased_date" in existing_settings:
            update_doc["plan_purchased_date"] = existing_settings["plan_purchased_date"]
        if "remaining_days" in existing_settings:
            update_doc["remaining_days"] = existing_settings["remaining_days"]
        if "paymentId" in existing_settings:
            update_doc["paymentId"] = existing_settings["paymentId"]
        if "orderId" in existing_settings:
            update_doc["orderId"] = existing_settings["orderId"]
    db["settings"].update_one(
        {"user_id": user_id},
        {"$set": update_doc},
        upsert=True
    )
    return {"message": "Settings updated successfully"}
    
@app.post("/api/change-password")
async def change_password(data: dict, token: str = Depends(oauth2_scheme)):
    payload = verify_access_token(token)
    user_id = payload.get("user_id")

    current_pwd = data.get("current")
    new_pwd = data.get("new")
    confirm_pwd = data.get("confirm")

    if not all([current_pwd, new_pwd, confirm_pwd]):
        raise HTTPException(status_code=400, detail="All fields required")

    if new_pwd != confirm_pwd:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    # Fetch user to verify current password
    db_user = db["users"].find_one({"_id": ObjectId(user_id)})
    if not db_user or not verify_password(current_pwd, db_user["password"]):
        raise HTTPException(status_code=400, detail="Current password incorrect")

    hashed = hash_password(new_pwd)
    db["users"].update_one({"_id": ObjectId(user_id)}, {"$set": {"password": hashed}})

    return {"message": "Password updated"}
@app.post("/api/auth/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest):
    # 1. Check if user exists
    user = db["users"].find_one({"email": payload.email})
    if not user:
        # Security tip: Don't reveal if email exists, but for dev we'll throw error
        raise HTTPException(status_code=404, detail="User with this email not found")

    # 2. Hash the new password
    hashed_password = hash_password(payload.new_password)

    # 3. Update in DB
    db["users"].update_one(
        {"email": payload.email},
        {"$set": {"password": hashed_password}}
    )

    return {"message": "Password has been reset successfully"}
# -----------------------
# Admin: User List
#-----------------------
@app.get("/api/admin/users")
def get_all_users(token: str = Depends(oauth2_scheme)):
    """Get all users for admin panel"""
    verify_access_token(token)
    users = list(db["users"].find({}, {"password": 0}).limit(50))
    for u in users:
        u["_id"] = str(u["_id"])
    return {"users": users, "count": len(users)}
@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are TrendBot, the official AI assistant for TrendAI. "
                               "You help users with sentiment analysis, market trends, and navigating the dashboard. "
                               "Keep your answers helpful, professional, and concise."
                },
                {
                    "role": "user",
                    "content": req.message,
                }
            ],
            model= "llama-3.1-8b-instant",
            temperature=0.7,
            max_tokens=500,
        )

        # 2. Extract the text response
        reply = chat_completion.choices[0].message.content
        return {"reply": reply}

    except Exception as e:
        logger.error(f"Chat Error: {str(e)}")
        return {"reply": "I'm having trouble thinking right now. Please try again in a moment."}

if __name__ == "__main__":
    import uvicorn
    print("\n[START] Starting TrendAI Server...")
    print("[STATS] API Documentation: http://localhost:8000/docs")
    print(" Server running at: http://localhost:8000\n")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
