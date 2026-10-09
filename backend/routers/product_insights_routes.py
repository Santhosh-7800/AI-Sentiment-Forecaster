"""
Product Insights Routes
Generate Groq-powered AI insights about products and sentiment analysis
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
import logging
import re
from oauth2 import verify_access_token
from fastapi.security import OAuth2PasswordBearer

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(
    prefix="/api/product-insights",
    tags=["Product Insights"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# Request/Response Models
class SentimentBreakdown(BaseModel):
    positive: int
    neutral: int
    negative: int


class ProductInsightsRequest(BaseModel):
    product: str = Field(..., min_length=2, max_length=100, description="Product name")
    sentiment_breakdown: SentimentBreakdown = Field(..., description="Sentiment counts")
    total_mentions: Optional[int] = Field(None, description="Total number of mentions")


class InsightsResponse(BaseModel):
    product: str
    product_overview: List[str] = Field(..., description="3-4 bullet points about the product")
    sentiment_analysis: List[str] = Field(..., description="2-3 points analyzing sentiment")
    recommendations: List[str] = Field(..., description="2-3 actionable recommendations")
    success: bool


def get_groq_llm():
    """Initialize Groq LLM with API key from environment"""
    try:
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY not configured in environment")

        from langchain_groq import ChatGroq
        llm = ChatGroq(
            groq_api_key=groq_api_key,
            model_name="llama-3.1-8b-instant",
            temperature=0.3,
            max_tokens=600
        )
        return llm
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Groq LLM library not installed. Run: pip install langchain-groq"
        )
    except Exception as e:
        logger.error(f"[FAIL] Failed to initialize Groq LLM: {e}")
        raise HTTPException(status_code=500, detail=f"LLM initialization failed: {str(e)}")


def parse_insights_response(response_text: str) -> Dict[str, List[str]]:
    """
    Parse Groq response into structured insights.
    Expected format:
    PRODUCT OVERVIEW:
    - point 1
    - point 2

    SENTIMENT ANALYSIS:
    - point 1
    - point 2

    RECOMMENDATIONS:
    - point 1
    - point 2
    """
    sections = {
        "product_overview": [],
        "sentiment_analysis": [],
        "recommendations": []
    }

    current_section = None
    lines = response_text.split("\n")

    def _clean_line(raw: str) -> str:
        # Remove markdown emphasis/header markers and leading bullet/index markers.
        text = raw.strip().replace("**", "")
        text = re.sub(r"^#+\s*", "", text)
        text = re.sub(r"^[-*•·]\s*", "", text)
        text = re.sub(r"^\d+[.)]\s*", "", text)
        return text.strip()

    def _is_list_point(raw: str) -> bool:
        return bool(re.match(r"^\s*([-*•·]|\d+[.)])\s+", raw or ""))

    for line in lines:
        raw = line.rstrip()
        cleaned = _clean_line(raw)
        if not cleaned:
            continue

        upper = cleaned.upper()
        if "PRODUCT OVERVIEW" in upper or "OVERVIEW" == upper:
            current_section = "product_overview"
            continue
        if "SENTIMENT ANALYSIS" in upper or "SENTIMENT" == upper:
            current_section = "sentiment_analysis"
            continue
        if "RECOMMENDATIONS" in upper or "RECOMMENDATION" in upper:
            current_section = "recommendations"
            continue

        # Accept list-style points and plain lines under an active section.
        if current_section and (_is_list_point(raw) or len(cleaned) > 8):
            sections[current_section].append(cleaned)

    # Fallback: if model ignored section formatting, capture top lines instead of empty placeholders.
    if not any(sections.values()):
        fallback_points = []
        for raw in lines:
            cleaned = _clean_line(raw)
            if cleaned and len(cleaned) > 8 and "IMPORTANT" not in cleaned.upper():
                fallback_points.append(cleaned)
        fallback_points = fallback_points[:6]
        if fallback_points:
            sections["product_overview"] = fallback_points[:2] or ["No specific insights generated"]
            sections["sentiment_analysis"] = fallback_points[2:4] or ["No specific insights generated"]
            sections["recommendations"] = fallback_points[4:6] or ["No specific insights generated"]

    # Ensure we have at least one point in each section
    for section in sections:
        if not sections[section]:
            sections[section] = ["No specific insights generated"]

    return sections


@router.post("/generate", response_model=InsightsResponse)
async def generate_product_insights(
    request: ProductInsightsRequest,
    token: str = Depends(oauth2_scheme)
) -> InsightsResponse:
    """
    Generate AI-powered insights about a product using Groq LLM.

    Analyzes product name and sentiment data to generate:
    - Product overview points
    - Sentiment analysis
    - Market recommendations
    """
    try:
        # Verify authentication
        try:
            verify_access_token(token)
        except Exception as e:
            raise HTTPException(status_code=401, detail="Unauthorized")

        # Calculate sentiment percentages
        total = request.sentiment_breakdown.positive + request.sentiment_breakdown.neutral + request.sentiment_breakdown.negative
        if total == 0:
            total = 1  # Avoid division by zero

        pos_pct = round((request.sentiment_breakdown.positive / total) * 100)
        neu_pct = round((request.sentiment_breakdown.neutral / total) * 100)
        neg_pct = round((request.sentiment_breakdown.negative / total) * 100)

        # Create prompt for Groq LLM
        prompt = f"""You are a market intelligence analyst specializing in consumer products.
Analyze the following product's sentiment data and provide SPECIFIC, ACTIONABLE insights.

Product: {request.product}
Sentiment Data:
- Positive mentions: {request.sentiment_breakdown.positive} ({pos_pct}%)
- Neutral mentions: {request.sentiment_breakdown.neutral} ({neu_pct}%)
- Negative mentions: {request.sentiment_breakdown.negative} ({neg_pct}%)

**IMPORTANT:** Generate specific insights based on what the sentiment numbers tell us. Be concrete and actionable.

PRODUCT OVERVIEW (2-3 bullet points - focus on what consumers are saying about the product):
- State a specific strength or weakness based on sentiment ratios
- Mention market reception or consumer perception
- Reference a typical use case or value proposition

SENTIMENT ANALYSIS (2-3 bullet points - interpret what the sentiment breakdown means):
- What does {pos_pct}% positive sentiment indicate?
- What consumer pain points drive the {neg_pct}% negative sentiment?
- Is the sentiment balanced, polarized, or overwhelmingly positive/negative?

RECOMMENDATIONS (2-3 bullet points - actionable next steps):
- Based on positive feedback, what should be marketed?
- Based on negative feedback, what needs improvement?
- What untapped market opportunity exists?

Format your response with section headers as shown. Be specific, not generic."""

        # Get Groq LLM instance
        llm = get_groq_llm()

        # Generate insights
        logger.info(f"[OK] Generating insights for product: {request.product}")
        response = llm.invoke(prompt)
        insights_text = response.content

        # Parse response
        parsed_insights = parse_insights_response(insights_text)

        logger.info(f"[OK] Successfully generated insights for {request.product}")

        return InsightsResponse(
            product=request.product,
            product_overview=parsed_insights["product_overview"],
            sentiment_analysis=parsed_insights["sentiment_analysis"],
            recommendations=parsed_insights["recommendations"],
            success=True
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[FAIL] Error generating product insights: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate insights: {str(e)}"
        )
