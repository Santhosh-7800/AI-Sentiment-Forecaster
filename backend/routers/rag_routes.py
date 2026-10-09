"""
RAG API Routes
FastAPI endpoints for RAG operations
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from oauth2 import verify_access_token
from fastapi.security import OAuth2PasswordBearer

from rag.rag_service import get_rag_engine
from rag.document_processor import DocumentProcessor
from pymongo import MongoClient

# Initialize router
router = APIRouter(
    prefix="/api/rag",
    tags=["RAG - Retrieval Augmented Generation"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# MongoDB connection (reuse from main server)
try:
    client = MongoClient(
        "mongodb+srv://DevanshVerma:qazxsw123@cluster0.fxr8rpr.mongodb.net/ai_project_db?retryWrites=true&w=majority&appName=Cluster0",
        serverSelectionTimeoutMS=5000
    )
    db = client["ai_project_db"]
    product_collection = db["reviews"]
    news_collection = db["news"]
except Exception as e:
    print(f"[WARN] MongoDB connection failed in RAG router: {e}")


# Request/Response Models
class QueryRequest(BaseModel):
    question: str = Field(..., description="User question")
    category: Optional[str] = Field(None, description="Filter by category")
    sentiment: Optional[str] = Field(None, description="Filter by sentiment")
    return_sources: bool = Field(True, description="Return source documents")


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: Optional[List[Dict[str, Any]]] = None
    source_count: Optional[int] = None
    success: bool


class IndexRequest(BaseModel):
    source: str = Field(..., description="Data source: 'mongodb' or 'all'")
    doc_type: Optional[str] = Field("all", description="Document type: 'review', 'news', or 'all'")
    limit: Optional[int] = Field(None, description="Limit number of documents to index")


class IndexResponse(BaseModel):
    success: bool
    message: str
    indexed_count: int
    errors: Optional[List[str]] = None


# -----------------------
# RAG Query Endpoints
# -----------------------

@router.get("/")
def rag_info():
    """Get RAG system information"""
    return {
        "message": "RAG (Retrieval-Augmented Generation) API",
        "version": "1.0.0",
        "endpoints": {
            "POST /query": "Ask questions with contextual retrieval",
            "POST /insights": "Get contextual insights",
            "POST /index/mongodb": "Index documents from MongoDB",
            "GET /sentiment-summary": "Get sentiment summary",
            "GET /trending-topics": "Get trending topics",
            "GET /stats": "Get RAG system statistics"
        }
    }


@router.post("/query", response_model=QueryResponse)
def query_rag(
    request: QueryRequest,
    token: str = Depends(oauth2_scheme)
):
    """
    Query the RAG system with natural language
    """
    verify_access_token(token)

    rag_engine = get_rag_engine()
    if not rag_engine:
        # Fallback: simple keyword search on MongoDB data
        return _simple_search_fallback(request)

    if request.category or request.sentiment:
        result = rag_engine.query_with_filters(
            question=request.question,
            category=request.category,
            sentiment=request.sentiment
        )
    else:
        result = rag_engine.query(
            question=request.question,
            return_sources=request.return_sources
        )

    return result


def _simple_search_fallback(request: QueryRequest) -> dict:
    """Simple keyword/category search on MongoDB when RAG is unavailable"""
    question_lower = request.question.lower()

    # Build a mongo text filter using the question keywords
    keywords = [w for w in question_lower.split() if len(w) > 3]

    # Determine category filter
    category_filter = {}
    if request.category:
        category_filter["category"] = request.category
    else:
        for kw in ["electronics", "clothes", "fashion", "essentials", "grocery"]:
            if kw in question_lower:
                category_filter["category"] = kw if kw not in ("fashion",) else "clothes"
                break

    # Determine sentiment filter
    sentiment_filter = {}
    if request.sentiment:
        sentiment_filter["sentiment_label"] = request.sentiment
    elif any(w in question_lower for w in ["positive", "good", "great"]):
        sentiment_filter["sentiment_label"] = "Positive"
    elif any(w in question_lower for w in ["negative", "bad", "poor"]):
        sentiment_filter["sentiment_label"] = "Negative"

    query = {**category_filter, **sentiment_filter}

    reviews = list(product_collection.find(query, {"_id": 0}).limit(200))
    news = list(news_collection.find({}, {"_id": 0}).limit(100))

    total = len(reviews)
    if total == 0:
        # Broaden the search  ignore filters
        reviews = list(product_collection.find({}, {"_id": 0}).limit(200))
        total = len(reviews)

    pos = sum(1 for r in reviews if r.get("sentiment_label") == "Positive")
    neg = sum(1 for r in reviews if r.get("sentiment_label") == "Negative")
    neu = sum(1 for r in reviews if r.get("sentiment_label") == "Neutral")

    categories = {}
    for r in reviews:
        cat = r.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1

    top_categories = sorted(categories.items(), key=lambda x: -x[1])[:3]
    cat_summary = ", ".join(f"{c}: {n}" for c, n in top_categories)

    context_label = "all products"
    if category_filter.get("category"):
        context_label = f"{category_filter['category']} products"

    if total == 0:
        answer = "No product reviews found in the database. Please run the scraper to populate data."
    else:
        pct_pos = round((pos / total) * 100)
        pct_neg = round((neg / total) * 100)
        pct_neu = round((neu / total) * 100)

        if pos >= neg and pos >= neu:
            overall = "predominantly positive"
        elif neg >= pos and neg >= neu:
            overall = "predominantly negative"
        else:
            overall = "mixed/neutral"

        answer = (
            f"Based on {total} reviews for {context_label}: "
            f"sentiment is {overall}  {pct_pos}% positive, {pct_neg}% negative, {pct_neu}% neutral. "
        )
        if top_categories:
            answer += f"Top reviewed categories: {cat_summary}. "

        # Add news insight if relevant
        news_pos = sum(1 for n in news if n.get("sentiment_label") == "Positive")
        news_neg = sum(1 for n in news if n.get("sentiment_label") == "Negative")
        if news:
            answer += (
                f"From {len(news)} news articles: {news_pos} positive and {news_neg} negative headlines. "
            )

        answer += (
            "\n\nNote: For deeper AI-powered analysis, configure a GROQ or OpenAI API key in the backend .env file."
        )

    return {
        "question": request.question,
        "answer": answer,
        "sources": [],
        "source_count": 0,
        "success": True,
    }


@router.post("/insights")
def get_insights(
    query: str,
    context_type: str = "all",
    token: str = Depends(oauth2_scheme)
):
    """
    Get contextual insights based on query
    
    Args:
        query: User query
        context_type: Type of context ('reviews', 'news', 'all')
    """
    verify_access_token(token)
    
    rag_engine = get_rag_engine()
    if not rag_engine:
        raise HTTPException(
            status_code=503,
            detail="RAG system not available"
        )
    
    return rag_engine.get_contextual_insights(query, context_type)


@router.get("/sentiment-summary")
def sentiment_summary(
    category: Optional[str] = None,
    token: str = Depends(oauth2_scheme)
):
    """
    Get sentiment summary for a category
    
    Args:
        category: Product category (optional)
    """
    verify_access_token(token)
    
    rag_engine = get_rag_engine()
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG system not available")
    
    return rag_engine.get_sentiment_summary(category)


@router.get("/trending-topics")
def trending_topics(
    limit: int = 5,
    token: str = Depends(oauth2_scheme)
):
    """
    Get trending topics from consumer discussions
    
    Args:
        limit: Number of topics to return
    """
    verify_access_token(token)
    
    rag_engine = get_rag_engine()
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG system not available")
    
    return rag_engine.get_trending_topics(limit)


@router.post("/compare-categories")
def compare_categories(
    categories: List[str],
    token: str = Depends(oauth2_scheme)
):
    """
    Compare sentiment across multiple categories
    
    Args:
        categories: List of categories to compare
    """
    verify_access_token(token)
    
    rag_engine = get_rag_engine()
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG system not available")
    
    return rag_engine.compare_products(categories)


# -----------------------
# Document Indexing Endpoints
# -----------------------

@router.post("/index/mongodb", response_model=IndexResponse)
def index_from_mongodb(
    request: IndexRequest,
    token: str = Depends(oauth2_scheme)
):
    """
    Index documents from MongoDB into vector store
    
    Example:
    ```
    {
        "source": "mongodb",
        "doc_type": "all",
        "limit": 100
    }
    ```
    """
    verify_access_token(token)
    
    rag_engine = get_rag_engine()
    if not rag_engine:
        raise HTTPException(
            status_code=503,
            detail="RAG system not initialized"
        )
    
    processor = DocumentProcessor()
    all_chunks = []
    errors = []
    
    try:
        # Index product reviews
        if request.doc_type in ["review", "all"]:
            try:
                reviews = list(product_collection.find().limit(request.limit or 0))
                if reviews:
                    review_chunks = processor.process_batch_from_mongodb(reviews, "review")
                    all_chunks.extend(review_chunks)
                    print(f"[OK] Processed {len(review_chunks)} review chunks")
            except Exception as e:
                errors.append(f"Error processing reviews: {str(e)}")
        
        # Index news articles
        if request.doc_type in ["news", "all"]:
            try:
                news = list(news_collection.find().limit(request.limit or 0))
                if news:
                    news_chunks = processor.process_batch_from_mongodb(news, "news")
                    all_chunks.extend(news_chunks)
                    print(f"[OK] Processed {len(news_chunks)} news chunks")
            except Exception as e:
                errors.append(f"Error processing news: {str(e)}")
        
        # Index documents
        if all_chunks:
            result = rag_engine.index_documents(all_chunks)
            
            return IndexResponse(
                success=result.get("success", False),
                message=f"Indexed {len(all_chunks)} document chunks from MongoDB",
                indexed_count=len(all_chunks),
                errors=errors if errors else None
            )
        else:
            return IndexResponse(
                success=False,
                message="No documents found to index",
                indexed_count=0,
                errors=errors if errors else None
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Indexing failed: {str(e)}"
        )


@router.get("/stats")
def get_stats(token: str = Depends(oauth2_scheme)):
    """Get RAG system statistics"""
    verify_access_token(token)
    
    rag_engine = get_rag_engine()
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG system not available")
    
    return rag_engine.get_stats()


@router.delete("/reset")
def reset_vector_store(token: str = Depends(oauth2_scheme)):
    """Reset/clear the vector store (admin only)"""
    verify_access_token(token)
    
    rag_engine = get_rag_engine()
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG system not available")
    
    try:
        rag_engine.vector_store_manager.delete_collection()
        return {"message": "Vector store cleared successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset vector store: {str(e)}"
        )
