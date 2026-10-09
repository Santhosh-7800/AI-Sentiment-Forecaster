"""
Custom Reports Routes
Persist user-created analysis reports (CSV uploads/imports) in MongoDB.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field

from database import db
from oauth2 import verify_access_token


router = APIRouter(prefix="/api/reports", tags=["Reports"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

reports_collection = db["custom_reports"]
trending_collection = db["trending_products"]


class CustomReportCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=150)
    tags: List[str] = Field(default_factory=list)
    source: str = Field(default="csv")
    rows: List[Dict[str, Any]] = Field(default_factory=list)


class CustomReportResponse(BaseModel):
    id: str
    title: str
    tags: List[str]
    source: str
    created_at: str
    summary: Dict[str, int]
    rows: List[Dict[str, Any]]


class TrendingImportRequest(BaseModel):
    mode: str = Field(default="single", description="single or all")
    product: Optional[str] = Field(default=None, description="product key for single mode")
    title: Optional[str] = Field(default=None, description="optional custom report title")


def _summarize_rows(rows: List[Dict[str, Any]]) -> Dict[str, int]:
    sentiment_keys = ["sentiment_label", "sentiment", "label", "polarity"]
    pos = 0
    neg = 0
    neu = 0

    for row in rows:
        value = ""
        for key in sentiment_keys:
            candidate = row.get(key)
            if isinstance(candidate, str) and candidate.strip():
                value = candidate
                break

        text = value.lower()
        if "pos" in text:
            pos += 1
        elif "neg" in text:
            neg += 1
        else:
            neu += 1

    return {
        "total": len(rows),
        "positive": pos,
        "negative": neg,
        "neutral": neu,
    }


def _insert_custom_report(user_id: str, title: str, tags: List[str], source: str, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    summary = _summarize_rows(rows)
    created_at = datetime.utcnow().isoformat()

    doc = {
        "user_id": user_id,
        "title": title,
        "tags": tags,
        "source": source,
        "rows": rows,
        "summary": summary,
        "created_at": created_at,
    }
    result = reports_collection.insert_one(doc)

    return {
        "id": str(result.inserted_id),
        "title": title,
        "tags": tags,
        "source": source,
        "created_at": created_at,
        "summary": summary,
        "rows": rows,
    }


@router.post("/custom", response_model=CustomReportResponse)
async def create_custom_report(payload: CustomReportCreateRequest, token: str = Depends(oauth2_scheme)):
    claims = verify_access_token(token)
    user_id = str(claims.get("user_id", ""))
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not payload.rows:
        raise HTTPException(status_code=400, detail="No rows found in report data")

    return _insert_custom_report(
        user_id=user_id,
        title=payload.title,
        tags=payload.tags,
        source=payload.source,
        rows=payload.rows,
    )


@router.post("/custom/from-trending")
async def create_report_from_trending(payload: TrendingImportRequest, token: str = Depends(oauth2_scheme)):
    claims = verify_access_token(token)
    user_id = str(claims.get("user_id", ""))
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    mode = (payload.mode or "single").lower().strip()
    if mode not in {"single", "all"}:
        raise HTTPException(status_code=400, detail="mode must be 'single' or 'all'")

    if mode == "single" and not (payload.product or "").strip():
        raise HTTPException(status_code=400, detail="product is required for single mode")

    today = datetime.utcnow().strftime("%Y-%m-%d")

    if mode == "all":
        docs = list(trending_collection.find({"date": today}).sort("last_updated", -1))
    else:
        p = (payload.product or "").strip()
        docs = list(
            trending_collection.find(
                {
                    "date": today,
                    "$or": [
                        {"product": {"$regex": p, "$options": "i"}},
                        {"keyword": {"$regex": p, "$options": "i"}},
                    ],
                }
            ).sort("last_updated", -1).limit(1)
        )

    if not docs:
        raise HTTPException(status_code=404, detail="No trending data found to import")

    rows: List[Dict[str, Any]] = []
    for d in docs:
        product_name = d.get("product", "")
        keyword = d.get("keyword", "")
        context_type = d.get("context_type", "News")
        articles = d.get("articles", []) or []

        for a in articles:
            rows.append(
                {
                    "product": product_name,
                    "keyword": keyword,
                    "context_type": context_type,
                    "title": a.get("title", ""),
                    "description": a.get("description", ""),
                    "source": a.get("source", ""),
                    "url": a.get("url", ""),
                    "published_at": a.get("published_at", ""),
                    "sentiment_label": a.get("sentiment_label", "Neutral"),
                    "sentiment_score": a.get("sentiment_score", 0),
                }
            )

    if not rows:
        raise HTTPException(status_code=404, detail="No trending reviews/articles available in selected data")

    default_title = "Trending Products Imported Analysis"
    if mode == "single":
        default_title = f"{docs[0].get('keyword') or docs[0].get('product') or 'Trending Product'} Imported Analysis"

    created = _insert_custom_report(
        user_id=user_id,
        title=(payload.title or default_title).strip(),
        tags=["Trending Products", "Imported", mode.upper()],
        source="trending_products",
        rows=rows,
    )

    return {
        "success": True,
        "mode": mode,
        "report": created,
        "imported_rows": len(rows),
        "products_count": len(docs),
    }


@router.get("/custom")
async def get_custom_reports(token: str = Depends(oauth2_scheme)):
    claims = verify_access_token(token)
    user_id = str(claims.get("user_id", ""))
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    docs = list(
        reports_collection.find(
            {"user_id": user_id},
            {"user_id": 0}
        ).sort("created_at", -1)
    )

    reports = []
    for d in docs:
        reports.append(
            {
                "id": str(d.get("_id")),
                "title": d.get("title", "Custom Analysis"),
                "tags": d.get("tags", []),
                "source": d.get("source", "csv"),
                "created_at": d.get("created_at", ""),
                "summary": d.get("summary", {"total": 0, "positive": 0, "negative": 0, "neutral": 0}),
                "rows": d.get("rows", []),
            }
        )

    return {"success": True, "data": reports}
