"""
Pipeline Management Routes
API endpoints for monitoring and controlling automated pipeline
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.automated_pipeline import pipeline
from services.quota_manager import quota_manager
from oauth2 import verify_access_token
from fastapi.security import OAuth2PasswordBearer
import logging
<<<<<<< HEAD
import re
=======
>>>>>>> 4463506 (Integrated TrendBot with Groq and polished UI styling)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/pipeline",
    tags=["Pipeline Management"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


<<<<<<< HEAD
_STOPWORDS = {
    "the", "a", "an", "and", "or", "for", "to", "of", "in", "on", "with", "from", "by", "at",
    "new", "latest", "best", "top", "trending", "popular", "product", "products", "news", "update"
}


def _detect_intent_from_text(text: str) -> str:
    t = (text or "").lower()
    if any(k in t for k in ["review", "hands-on", "rating", "verdict", "test"]):
        return "Reviews"
    if any(k in t for k in ["launch", "launched", "release", "released", "debut", "unveil"]):
        return "Launch"
    if any(k in t for k in ["price", "pricing", "cost", "deal", "discount"]):
        return "Pricing"
    if any(k in t for k in ["compare", "comparison", "vs"]):
        return "Comparisons"
    if any(k in t for k in ["leak", "rumor", "rumour", "teaser"]):
        return "Leaks"
    return "News"


def _derive_legacy_context(doc: dict) -> dict:
    articles = doc.get("articles") or []
    sample_text = " ".join([f"{a.get('title', '')} {a.get('description', '')}" for a in articles[:3]])
    intent = doc.get("context_type") or _detect_intent_from_text(sample_text)

    # Prefer precomputed keyword; else clean product string.
    base_keyword = doc.get("keyword") or _clean_heading_keyword(doc.get("product", ""))

    # If the keyword is noisy legacy data, recompute from product text.
    if base_keyword and len(base_keyword.split()) > 5:
        base_keyword = _clean_heading_keyword(base_keyword)

    if intent and intent != "News" and " - " not in base_keyword:
        keyword = f"{base_keyword} - {intent}"
    else:
        keyword = base_keyword

    return {
        "keyword": keyword,
        "context_type": intent,
        "context_category": doc.get("context_category", "Tech Products"),
        "context_region": doc.get("context_region", ""),
        "context_brand": doc.get("context_brand", ""),
    }


def _clean_heading_keyword(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", re.sub(r"[^A-Za-z0-9\s]", " ", value or "")).strip()
    if not cleaned:
        return "Unknown Keyword"

    words = [w for w in cleaned.split() if w.lower() not in _STOPWORDS]
    if not words:
        words = cleaned.split()

    if len(words) > 3:
        words = words[:3]
    return " ".join(words).title()


=======
>>>>>>> 4463506 (Integrated TrendBot with Groq and polished UI styling)
class PipelineStatus(BaseModel):
    running: bool
    scheduler_status: str
    quota_status: dict
    last_run: str


@router.get("/status")
async def get_pipeline_status() -> dict:
    """Get current pipeline status and quota information"""
    try:
        status = pipeline.get_status()
        return {
            "success": True,
            "pipeline": status,
            "timestamp": __import__("datetime").datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"[FAIL] Error getting pipeline status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pipeline status")


@router.get("/quota")
async def get_quota_status() -> dict:
    """Get API quota status"""
    try:
        return {
            "success": True,
            "newsapi": quota_manager.get_status("newsapi"),
<<<<<<< HEAD
            "gnews": quota_manager.get_status("gnews"),
=======
>>>>>>> 4463506 (Integrated TrendBot with Groq and polished UI styling)
            "gemini": quota_manager.get_status("gemini"),
            "timestamp": __import__("datetime").datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"[FAIL] Error getting quota status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get quota status")


@router.post("/run-now")
async def trigger_pipeline_now(token: str = None) -> dict:
    """
    Manually trigger the automated pipeline (admin only)
    """
    try:
        # Optional token auth for deployment
        if token:
            try:
                verify_access_token(token)
            except:
                raise HTTPException(status_code=401, detail="Unauthorized")

<<<<<<< HEAD
        logger.info("[MANUAL] Triggering pipeline manually with provider rotation")
        pipeline.run_daily_update(rotate_provider=True)
=======
        logger.info("[MANUAL] Triggering pipeline manually")
        pipeline.run_daily_update()
>>>>>>> 4463506 (Integrated TrendBot with Groq and polished UI styling)

        return {
            "success": True,
            "message": "Pipeline triggered successfully",
            "timestamp": __import__("datetime").datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"[FAIL] Error triggering pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest-data")
async def get_latest_analyzed_data(product: str = None) -> dict:
    """
    Get latest analyzed trending data from MongoDB
    Optionally filter by product name
    """
    try:
        from database import db

        collection = db["trending_products"]

        if product:
<<<<<<< HEAD
            data = collection.find_one(
                {
                    "$or": [
                        {"product": {"$regex": product, "$options": "i"}},
                        {"keyword": {"$regex": product, "$options": "i"}},
                    ]
                }
            )
=======
            data = collection.find_one({"product": {"$regex": product, "$options": "i"}})
>>>>>>> 4463506 (Integrated TrendBot with Groq and polished UI styling)
            if not data:
                return {"success": True, "data": None, "message": "No data found for product"}
        else:
            # Get all trending products from today
            import datetime
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            data = list(collection.find({"date": today}).limit(10))

<<<<<<< HEAD
        normalized_docs = []
        for d in (data if isinstance(data, list) else [data]):
            legacy_context = _derive_legacy_context(d)
            normalized_docs.append(
                {
                    "product": d.get("product"),
                    "keyword": legacy_context["keyword"],
                    "context_type": legacy_context["context_type"],
                    "context_category": legacy_context["context_category"],
                    "context_region": legacy_context["context_region"],
                    "context_brand": legacy_context["context_brand"],
=======
        return {
            "success": True,
            "data": [
                {
                    "product": d.get("product"),
>>>>>>> 4463506 (Integrated TrendBot with Groq and polished UI styling)
                    "date": d.get("date"),
                    "article_count": d.get("article_count", 0),
                    "positive_count": d.get("positive_count", 0),
                    "negative_count": d.get("negative_count", 0),
                    "neutral_count": d.get("neutral_count", 0),
<<<<<<< HEAD
                    "last_updated": d.get("last_updated"),
                    "search_queries": d.get("search_queries", []),
                }
            )

        return {
            "success": True,
            "data": normalized_docs,
=======
                    "last_updated": d.get("last_updated")
                }
                for d in (data if isinstance(data, list) else [data])
            ]
>>>>>>> 4463506 (Integrated TrendBot with Groq and polished UI styling)
        }
    except Exception as e:
        logger.error(f"[FAIL] Error getting latest data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get latest data")
