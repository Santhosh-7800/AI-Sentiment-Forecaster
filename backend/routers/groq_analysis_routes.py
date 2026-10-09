"""
Groq Analysis API Routes
Endpoints for generating AI-powered product and sentiment insights
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from services.groq_analysis_service import get_analysis_service
from oauth2 import verify_access_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/product-insights", tags=["product-insights"])


# Request/Response Models
class SentimentBreakdown(BaseModel):
    """Sentiment breakdown data"""
    positive: int = Field(ge=0)
    neutral: int = Field(ge=0)
    negative: int = Field(ge=0)


class PriceSensitivityData(BaseModel):
    """Price sensitivity analysis"""
    price_positive_mentions: int = Field(ge=0)
    price_negative_mentions: int = Field(ge=0)
    price_sensitivity_index: float = Field(default=0.0)


class DailyTrendData(BaseModel):
    """Daily sentiment trend"""
    date: str
    score: float
    samples: int = 0


class ProductInsightsRequest(BaseModel):
    """Request to generate product insights"""
    product: str = Field(..., min_length=1, max_length=100)
    sentiment_breakdown: SentimentBreakdown
    article_count: int = Field(default=0, ge=0)
    price_sensitivity: Optional[PriceSensitivityData] = None
    daily_trend: Optional[List[DailyTrendData]] = None


class InsightsResponse(BaseModel):
    """Response with generated insights"""
    product: str
    product_overview: List[str]
    sentiment_analysis: List[str]
    recommendations: List[str]
    generated_at: str


class SentimentInsightsRequest(BaseModel):
    """Request to generate sentiment-specific insights"""
    sentiment_breakdown: SentimentBreakdown
    category: str = Field(default="all products", max_length=100)


class SentimentInsightsResponse(BaseModel):
    """Response with sentiment insights"""
    category: str
    insights: List[str]
    generated_at: str


@router.post("/generate", response_model=InsightsResponse)
async def generate_product_insights(
    request: ProductInsightsRequest,
    token: str = Depends(verify_access_token)
) -> InsightsResponse:
    """
    Generate comprehensive product insights using Groq LLM

    **Parameters:**
    - `product`: Product name or category
    - `sentiment_breakdown`: Sentiment analysis data (positive, neutral, negative counts)
    - `article_count`: Total articles analyzed
    - `price_sensitivity`: Optional price analysis data
    - `daily_trend`: Optional daily trend data

    **Returns:** Product overview, sentiment analysis, and market recommendations
    """
    try:
        service = get_analysis_service()

        if not service.llm:
            raise HTTPException(
                status_code=503,
                detail="Groq LLM service unavailable. Please ensure backend Groq is configured."
            )

        # Convert request data
        sentiment_dict = {
            "positive": request.sentiment_breakdown.positive,
            "neutral": request.sentiment_breakdown.neutral,
            "negative": request.sentiment_breakdown.negative
        }

        price_data = None
        if request.price_sensitivity:
            price_data = {
                "price_positive_mentions": request.price_sensitivity.price_positive_mentions,
                "price_negative_mentions": request.price_sensitivity.price_negative_mentions,
                "price_sensitivity_index": request.price_sensitivity.price_sensitivity_index
            }

        daily_data = None
        if request.daily_trend:
            daily_data = [
                {
                    "date": item.date,
                    "score": item.score,
                    "samples": item.samples
                }
                for item in request.daily_trend
            ]

        # Generate insights
        insights = service.generate_product_insights(
            product=request.product,
            sentiment_breakdown=sentiment_dict,
            article_count=request.article_count,
            price_sensitivity=price_data,
            daily_trend=daily_data
        )

        from datetime import datetime

        return InsightsResponse(
            product=request.product,
            product_overview=insights.get("product_overview", []),
            sentiment_analysis=insights.get("sentiment_analysis", []),
            recommendations=insights.get("recommendations", []),
            generated_at=datetime.utcnow().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating insights: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating insights: {str(e)}"
        )


@router.post("/sentiment-insights", response_model=SentimentInsightsResponse)
async def generate_sentiment_insights(
    request: SentimentInsightsRequest,
    token: str = Depends(verify_access_token)
) -> SentimentInsightsResponse:
    """
    Generate sentiment-specific insights and analysis

    **Parameters:**
    - `sentiment_breakdown`: Sentiment data (positive, neutral, negative)
    - `category`: Product category or name (default: "all products")

    **Returns:** List of sentiment-specific insights
    """
    try:
        service = get_analysis_service()

        if not service.llm:
            raise HTTPException(
                status_code=503,
                detail="Groq LLM service unavailable"
            )

        sentiment_dict = {
            "positive": request.sentiment_breakdown.positive,
            "neutral": request.sentiment_breakdown.neutral,
            "negative": request.sentiment_breakdown.negative
        }

        insights = service.generate_sentiment_insights(
            sentiment_breakdown=sentiment_dict,
            category=request.category
        )

        from datetime import datetime

        return SentimentInsightsResponse(
            category=request.category,
            insights=insights,
            generated_at=datetime.utcnow().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating sentiment insights: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating sentiment insights: {str(e)}"
        )


@router.get("/health")
async def health_check(token: str = Depends(verify_access_token)) -> Dict[str, Any]:
    """Check if Groq analysis service is available"""
    service = get_analysis_service()
    return {
        "status": "healthy" if service.llm else "unavailable",
        "service": "groq_analysis",
        "llm_initialized": service.llm is not None
    }
