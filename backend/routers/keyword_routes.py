"""
Keyword Analysis API Routes
Endpoints for keyword extraction and analysis
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging

from services.keyword_analysis import get_keyword_analyzer
from oauth2 import verify_access_token

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/keywords",
    tags=["Keyword Analysis"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class KeywordRequest(BaseModel):
    """Request model for keyword extraction"""
    text: str = Field(..., min_length=1, description="Text to extract keywords from")
    method: str = Field("auto", description="Extraction method: auto, yake, frequency, ngram")
    max_keywords: int = Field(10, ge=1, le=50, description="Maximum number of keywords")
    min_word_length: int = Field(3, ge=1, le=20, description="Minimum word length")


class KeywordBatchRequest(BaseModel):
    """Request model for batch keyword analysis"""
    texts: List[str] = Field(..., min_length=1, description="List of texts to analyze")
    max_keywords: int = Field(10, ge=1, le=50, description="Maximum keywords per text")


class KeywordResponse(BaseModel):
    """Response model for keyword extraction"""
    keywords: List[Dict[str, Any]]
    total_keywords: int
    method: str


@router.post("/extract", response_model=KeywordResponse)
async def extract_keywords(
    request: KeywordRequest,
    token: str = Depends(oauth2_scheme)
):
    """
    Extract keywords from a single text

    - **text**: Input text
    - **method**: auto (default), yake, frequency, or ngram
    - **max_keywords**: Maximum number of keywords (1-50)
    - **min_word_length**: Minimum word length (default: 3)
    """
    verify_access_token(token)

    try:
        analyzer = get_keyword_analyzer()

        keywords = analyzer.extract_keywords(
            text=request.text,
            method=request.method,
            max_keywords=request.max_keywords,
            min_word_length=request.min_word_length
        )

        return {
            "keywords": keywords,
            "total_keywords": len(keywords),
            "method": request.method
        }

    except Exception as e:
        logger.error(f"Keyword extraction error: {e}")
        raise HTTPException(status_code=500, detail=f"Keyword extraction failed: {str(e)}")


@router.post("/batch")
async def analyze_keywords_batch(
    request: KeywordBatchRequest,
    token: str = Depends(oauth2_scheme)
):
    """
    Analyze keywords across multiple texts

    Returns aggregated keyword analysis with frequencies
    """
    verify_access_token(token)

    try:
        analyzer = get_keyword_analyzer()

        result = analyzer.analyze_keywords_batch(
            texts=request.texts,
            max_keywords=request.max_keywords
        )

        return result

    except Exception as e:
        logger.error(f"Batch keyword analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")


@router.get("/methods")
async def get_available_methods(token: str = Depends(oauth2_scheme)):
    """
    Get list of available keyword extraction methods
    """
    verify_access_token(token)

    try:
        from services.keyword_analysis import YAKE_AVAILABLE, SKLEARN_AVAILABLE

        methods = {
            "auto": {
                "name": "Auto",
                "description": "Automatically selects the best available method",
                "available": True
            },
            "yake": {
                "name": "YAKE",
                "description": "Yet Another Keyword Extractor - advanced algorithm",
                "available": YAKE_AVAILABLE
            },
            "frequency": {
                "name": "Frequency",
                "description": "Simple frequency-based extraction",
                "available": True
            },
            "ngram": {
                "name": "N-Gram",
                "description": "Extract 2-3 word phrases",
                "available": True
            }
        }

        return {
            "methods": methods,
            "default": "auto",
            "recommended": "yake" if YAKE_AVAILABLE else "frequency"
        }

    except Exception as e:
        logger.error(f"Get methods error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_keyword_stats(token: str = Depends(oauth2_scheme)):
    """
    Get keyword analysis statistics
    """
    verify_access_token(token)

    return {
        "service": "keyword_analysis",
        "status": "active",
        "available_methods": ["auto", "yake", "frequency", "ngram"],
        "default_method": "auto",
        "max_keywords_limit": 50,
        "min_word_length_default": 3
    }
