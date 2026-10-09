"""
Analytics API Routes
Exposes sentiment analysis, topic modeling, trends, and alerts
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Dict, Any

from services.enhanced_sentiment import get_sentiment_analyzer
from services.topic_modeling import get_topic_service
from services.trend_analytics import get_trend_engine
from services.alerts import get_alert_system
from services.report_generation import get_report_generator
from oauth2 import verify_access_token
from fastapi.security import OAuth2PasswordBearer

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/analytics",
    tags=["Analytics & Insights"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# Request/Response Models
class AnalyzeSentimentRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=5000)
    aspect_based: bool = Field(default=True)


class TopicAnalysisRequest(BaseModel):
    texts: List[str] = Field(..., min_items=3)
    product: str = Field(..., min_length=2, max_length=100)


class TrendAnalysisRequest(BaseModel):
    sentiments: List[float] = Field(..., min_items=2)
    dates: List[str] = Field(..., min_items=2)
    product: str = Field(..., min_length=2, max_length=100)


class AlertAckRequest(BaseModel):
    alert_id: str


class ReportGenerateRequest(BaseModel):
    product: str = Field(..., min_length=2)
    analysis_data: Dict[str, Any]
    format: str = Field(default="pdf")  # pdf or excel


# Sentiment Analysis Endpoints
@router.post("/sentiment/enhanced")
async def analyze_enhanced_sentiment(request: AnalyzeSentimentRequest, token: str = Depends(oauth2_scheme)):
    """
    Analyze sentiment with emotions and aspects
    
    Returns:
    - Overall sentiment (positive/neutral/negative)
    - Emotion breakdown (joy, anger, sadness, etc.)
    - Aspect-based sentiment (quality, price, performance, etc.)
    - Confidence scores
    """
    verify_access_token(token)
    
    try:
        analyzer = get_sentiment_analyzer()
        result = analyzer.analyze(request.text)
        
        logger.info(f"Enhanced sentiment analyzed, label={result['label']}")
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        logger.error(f"Sentiment analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sentiment/batch")
async def analyze_batch_sentiment(texts: List[str], token: str = Depends(oauth2_scheme)):
    """
    Analyze multiple texts efficiently
    
    Returns aggregated sentiment metrics
    """
    verify_access_token(token)
    
    try:
        if not texts or len(texts) < 1:
            raise ValueError("At least 1 text is required")
        
        analyzer = get_sentiment_analyzer()
        results = analyzer.analyze_batch(texts[:50])  # Limit to 50
        aggregated = analyzer.aggregate_sentiments(results)
        
        return {
            "status": "success",
            "individual_results": results,
            "aggregated": aggregated
        }
    except Exception as e:
        logger.error(f"Batch sentiment error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Topic Modeling Endpoints
@router.post("/topics/extract")
async def extract_topics(request: TopicAnalysisRequest, token: str = Depends(oauth2_scheme)):
    """
    Extract topics from review texts
    
    Returns:
    - Top 5 topics with keywords
    - Document count per topic
    - Topic strength scores
    """
    verify_access_token(token)
    
    try:
        service = get_topic_service()
        topics = service.train_topics(request.texts, request.product)
        
        logger.info(f"Extracted {len(topics['topics'])} topics for {request.product}")
        return {
            "status": "success",
            "product": request.product,
            "data": topics
        }
    except Exception as e:
        logger.error(f"Topic extraction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/topics/evolution")
async def analyze_topic_evolution(texts: List[str], dates: List[str], product: str, token: str = Depends(oauth2_scheme)):
    """
    Analyze how topics evolve over time
    
    Returns:
    - Topic distribution by time period
    - Emerging topics
    - Declining topics
    """
    verify_access_token(token)
    
    try:
        if len(texts) != len(dates):
            raise ValueError("texts and dates must be equal length")
        
        service = get_topic_service()
        evolution = service.analyze_topic_evolution(texts, dates)
        
        return {
            "status": "success",
            "product": product,
            "data": evolution
        }
    except Exception as e:
        logger.error(f"Topic evolution error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Trend Analysis Endpoints
@router.post("/trends/analyze")
async def analyze_trends(request: TrendAnalysisRequest, token: str = Depends(oauth2_scheme)):
    """
    Analyze sentiment trends with anomaly detection and forecasting
    
    Returns:
    - Trend direction (increasing/decreasing/stable)
    - Volatility metrics
    - 30-day forecast
    - Anomaly detection
    """
    verify_access_token(token)
    
    try:
        engine = get_trend_engine()
        analysis = engine.analyze_sentiment_trend(request.sentiments, request.dates)
        
        logger.info(f"Trend analyzed for {request.product}: {analysis.get('trend', {}).get('direction')}")
        return {
            "status": "success",
            "product": request.product,
            "data": analysis
        }
    except Exception as e:
        logger.error(f"Trend analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trends/spikes")
async def detect_sentiment_spikes(sentiments: List[float], threshold: float = 20.0, token: str = Depends(oauth2_scheme)):
    """
    Detect sudden sentiment changes
    
    Returns:
    - Spike events with severity
    - Direction (positive/negative)
    - Percentage change
    """
    verify_access_token(token)
    
    try:
        engine = get_trend_engine()
        spikes = engine.detect_sentiment_spikes(sentiments, threshold)
        
        return {
            "status": "success",
            "spike_count": len(spikes),
            "spikes": spikes
        }
    except Exception as e:
        logger.error(f"Spike detection error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trends/compare")
async def compare_products(products: Dict[str, List[float]], dates: List[str], token: str = Depends(oauth2_scheme)):
    """
    Compare sentiment trends across multiple products
    
    Returns:
    - Best performer
    - Worst performer
    - Most volatile product
    """
    verify_access_token(token)
    
    try:
        engine = get_trend_engine()
        comparison = engine.compare_product_trends(products, dates)
        
        return {
            "status": "success",
            "data": comparison
        }
    except Exception as e:
        logger.error(f"Product comparison error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Alert Endpoints
@router.get("/alerts/active")
async def get_active_alerts(product: str = None, severity: str = None, token: str = Depends(oauth2_scheme)):
    """
    Get active alerts
    
    Filters:
    - product: Filter by product name
    - severity: critical, warning, or info
    """
    verify_access_token(token)
    
    try:
        alert_system = get_alert_system()
        
        # Map severity string to enum
        severity_enum = None
        if severity:
            from services.alerts import AlertSeverity
            severity_enum = AlertSeverity(severity.lower())
        
        alerts = alert_system.get_active_alerts(product=product, severity=severity_enum)
        
        return {
            "status": "success",
            "count": len(alerts),
            "alerts": alerts
        }
    except Exception as e:
        logger.error(f"Get alerts error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/acknowledge")
async def acknowledge_alert(request: AlertAckRequest, token: str = Depends(oauth2_scheme)):
    """
    Mark alert as acknowledged
    """
    verify_access_token(token)
    
    try:
        alert_system = get_alert_system()
        success = alert_system.acknowledge_alert(request.alert_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {
            "status": "success",
            "message": "Alert acknowledged"
        }
    except Exception as e:
        logger.error(f"Acknowledge alert error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts/stats")
async def get_alert_stats(token: str = Depends(oauth2_scheme)):
    """
    Get alert system statistics
    """
    verify_access_token(token)
    
    try:
        alert_system = get_alert_system()
        stats = alert_system.get_alert_stats()
        
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        logger.error(f"Alert stats error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts/digest")
async def get_daily_digest(product: str = None, token: str = Depends(oauth2_scheme)):
    """
    Get daily alert digest
    """
    verify_access_token(token)
    
    try:
        alert_system = get_alert_system()
        digest = alert_system.generate_daily_digest(product=product)
        
        return {
            "status": "success",
            "data": digest
        }
    except Exception as e:
        logger.error(f"Digest error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Report Generation Endpoints
@router.post("/reports/generate")
async def generate_report(request: ReportGenerateRequest, token: str = Depends(oauth2_scheme)):
    """
    Generate PDF or Excel report
    
    Formats:
    - pdf: PDF report with charts and insights
    - excel: Excel workbook with detailed data
    """
    verify_access_token(token)
    
    try:
        gen = get_report_generator()
        
        if request.format.lower() == "pdf":
            filepath = gen.generate_pdf_report(request.product, request.analysis_data)
        elif request.format.lower() == "excel":
            filepath = gen.generate_excel_report(request.product, request.analysis_data)
        else:
            raise ValueError(f"Unsupported format: {request.format}")
        
        if not filepath:
            raise HTTPException(status_code=500, detail="Report generation failed")
        
        return {
            "status": "success",
            "filepath": filepath,
            "format": request.format,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Report generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reports/batch")
async def generate_batch_report(products: Dict[str, Dict[str, Any]], token: str = Depends(oauth2_scheme)):
    """
    Generate comparison report for multiple products
    """
    verify_access_token(token)
    
    try:
        gen = get_report_generator()
        filepath = gen.generate_batch_report(products)
        
        if not filepath:
            raise HTTPException(status_code=500, detail="Report generation failed")
        
        return {
            "status": "success",
            "filepath": filepath,
            "products_compared": len(products),
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Batch report error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Health & Info Endpoints
@router.get("/info")
async def analytics_info(token: str = Depends(oauth2_scheme)):
    """Get available analytics capabilities"""
    verify_access_token(token)
    
    return {
        "status": "success",
        "capabilities": {
            "sentiment_analysis": {
                "base": True,
                "emotion_detection": True,
                "aspect_based": True,
                "batch_processing": True
            },
            "topic_modeling": {
                "extraction": True,
                "evolution_tracking": True,
                "max_topics": 5
            },
            "trend_analysis": {
                "trend_direction": True,
                "volatility_analysis": True,
                "anomaly_detection": True,
                "forecasting": True,
                "forecast_days": 30
            },
            "alerts": {
                "sentiment_spikes": True,
                "trend_changes": True,
                "topic_surges": True,
                "daily_digest": True
            },
            "reporting": {
                "pdf": True,
                "excel": True,
                "batch_reports": True
            }
        },
        "version": "1.0.0"
    }
