"""
Enhanced Sentiment Analysis Service
Provides aspect-based sentiment, emotion detection, and detailed scoring
Uses lightweight VADER for fast processing
"""
import logging
import re
from typing import Dict, List, Any
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob

logger = logging.getLogger(__name__)

class EnhancedSentimentAnalyzer:
    """Advanced sentiment analysis with emotions and aspects"""

    def __init__(self):
        """Initialize sentiment analyzer"""
        logger.info("Loading enhanced sentiment analyzer...")

        # Use VADER instead of heavy transformer model
        self.sentiment_analyzer = SentimentIntensityAnalyzer()

        # Emotion detection - use keyword-based approach
        self.emotion_classifier = None
        self.emotions_available = False  # Use keyword-based fallback

        logger.info("Enhanced sentiment analyzer initialized (lightweight VADER)")
        self.aspect_keywords = self._init_aspect_keywords()
    
    def _init_aspect_keywords(self) -> Dict[str, List[str]]:
        """Initialize aspect-based keyword mapping"""
        return {
            "quality": ["quality", "durable", "build", "construction", "material", "craftsmanship", "solid", "sturdy"],
            "price": ["price", "cost", "expensive", "affordable", "deal", "worth", "value", "overpriced"],
            "performance": ["fast", "slow", "lag", "smooth", "responsive", "speed", "efficient", "powerful"],
            "design": ["design", "look", "appearance", "aesthetic", "color", "size", "weight", "feel"],
            "battery": ["battery", "power", "charging", "stamina", "longevity", "runtime", "endurance"],
            "camera": ["camera", "photo", "video", "lens", "clarity", "resolution", "picture", "image"],
            "screen": ["screen", "display", "brightness", "color", "resolution", "refresh", "clarity"],
            "customer_service": ["service", "support", "customer", "return", "warranty", "help", "delivery"],
            "reliability": ["reliable", "broken", "defect", "issue", "problem", "crash", "fail", "error"]
        }
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Comprehensive sentiment analysis
        
        Args:
            text: Review text to analyze
        
        Returns:
            Detailed sentiment breakdown
        """
        try:
            # Limit text length
            text = text[:512] if len(text) > 512 else text
            
            # Basic sentiment
            sentiment_result = self._get_base_sentiment(text)
            
            # Emotion detection
            emotions = self._detect_emotions(text)
            
            # Aspect-based sentiment
            aspects = self._analyze_aspects(text)
            
            # Subjectivity and polarity
            subjectivity = self._calculate_subjectivity(text)
            
            return {
                "overall": sentiment_result,
                "emotions": emotions,
                "aspects": aspects,
                "subjectivity": subjectivity,
                "confidence_score": sentiment_result.get("confidence_score", 0),
                "label": sentiment_result.get("label", "Neutral")
            }
        except Exception as e:
            logger.error(f"Sentiment analysis error: {str(e)}")
            return self._empty_sentiment()
    
    def _get_base_sentiment(self, text: str) -> Dict[str, Any]:
        """Get base sentiment classification using VADER"""
        try:
            # Use VADER for sentiment
            scores = self.sentiment_analyzer.polarity_scores(text)

            # VADER returns: neg, neu, pos (0-1), compound (-1 to 1)
            neg_pct = scores["neg"] * 100
            neu_pct = scores["neu"] * 100
            pos_pct = scores["pos"] * 100
            compound = scores["compound"]

            # Determine label based on compound score
            if compound >= 0.05:
                label = "Positive"
            elif compound <= -0.05:
                label = "Negative"
            else:
                label = "Neutral"

            formatted = {
                "Negative": round(neg_pct, 2),
                "Neutral": round(neu_pct, 2),
                "Positive": round(pos_pct, 2)
            }

            return {
                "label": label,
                "confidence_score": round(max(neg_pct, neu_pct, pos_pct) / 100, 4),
                "percentages": formatted,
                "score": round(compound, 4)
            }
        except Exception as e:
            logger.error(f"Base sentiment error: {str(e)}")
            return {
                "label": "Neutral",
                "confidence_score": 0.0,
                "percentages": {"Positive": 0, "Neutral": 100, "Negative": 0},
                "score": 0.0
            }
    
    def _detect_emotions(self, text: str) -> Dict[str, float]:
        """Detect emotions in text"""
        if not self.emotions_available:
            return self._fallback_emotions(text)
        
        try:
            result = self.emotion_classifier(text)
            emotions = {}
            for emotion in result:
                label = emotion["label"].lower()
                score = emotion["score"]
                emotions[label] = round(score, 3)
            
            return emotions
        except Exception as e:
            logger.error(f"Emotion detection error: {str(e)}")
            return self._fallback_emotions(text)
    
    def _fallback_emotions(self, text: str) -> Dict[str, float]:
        """Fallback emotion detection using keywords"""
        emotions = {
            "joy": 0.0, "anger": 0.0, "sadness": 0.0,
            "surprise": 0.0, "fear": 0.0, "disgust": 0.0
        }
        
        text_lower = text.lower()
        
        # Keyword-based fallback
        emotion_keywords = {
            "joy": ["happy", "great", "love", "amazing", "excellent", "wonderful", "perfect"],
            "anger": ["angry", "hate", "frustrated", "terrible", "awful", "disgusted"],
            "sadness": ["sad", "disappointed", "upset", "depressed", "down"],
            "surprise": ["surprised", "shocked", "unexpected", "amazing"],
            "fear": ["afraid", "scared", "worried", "nervous"],
            "disgust": ["disgusting", "gross", "yuck", "repulsive"]
        }
        
        for emotion, keywords in emotion_keywords.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            emotions[emotion] = min(matches * 0.15, 1.0)  # Cap at 1.0
        
        # Normalize
        total = sum(emotions.values())
        if total > 0:
            emotions = {k: round(v / total, 3) for k, v in emotions.items()}
        
        return emotions
    
    def _analyze_aspects(self, text: str) -> Dict[str, Any]:
        """Analyze aspects mentioned in review"""
        aspects_found = {}
        text_lower = text.lower()
        
        for aspect, keywords in self.aspect_keywords.items():
            matches = [kw for kw in keywords if kw in text_lower]
            if matches:
                # Determine aspect sentiment
                aspect_text = " ".join([text_lower[max(0, text_lower.find(kw)-30):text_lower.find(kw)+30] 
                                       for kw in matches if kw in text_lower])
                
                sentiment = self._get_base_sentiment(aspect_text)
                
                aspects_found[aspect] = {
                    "mentioned": True,
                    "keywords": list(set(matches)),
                    "sentiment": sentiment["label"],
                    "confidence": sentiment["confidence_score"],
                    "score": sentiment["score"]
                }
        
        return aspects_found
    
    def _calculate_subjectivity(self, text: str) -> float:
        """Calculate subjectivity score (0-1, where 1 is very subjective)"""
        try:
            blob = TextBlob(text)
            return round(blob.sentiment.subjectivity, 3)
        except:
            # Fallback: count opinion words
            opinion_words = ["think", "feel", "believe", "opinion", "seem", "appear"]
            count = sum(1 for word in opinion_words if word in text.lower())
            return min(count * 0.1, 1.0)
    
    def _empty_sentiment(self) -> Dict[str, Any]:
        """Return empty sentiment response"""
        return {
            "overall": {
                "label": "Neutral",
                "confidence_score": 0.0,
                "percentages": {"Positive": 0, "Neutral": 100, "Negative": 0},
                "score": 0.0
            },
            "emotions": {"joy": 0.0, "anger": 0.0, "sadness": 0.0},
            "aspects": {},
            "subjectivity": 0.0,
            "confidence_score": 0.0,
            "label": "Neutral"
        }
    
    def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Analyze multiple texts efficiently"""
        results = []
        for text in texts:
            results.append(self.analyze(text))
        return results
    
    def aggregate_sentiments(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate multiple sentiment analyses"""
        if not results:
            return {"aggregated": {}, "stats": {}}
        
        # Calculate averages
        sentiment_scores = [r["overall"]["score"] for r in results]
        emotions_list = [r["emotions"] for r in results]
        
        # Aggregate emotions
        aggregated_emotions = {}
        if emotions_list and emotions_list[0]:
            for emotion in emotions_list[0].keys():
                values = [e.get(emotion, 0) for e in emotions_list]
                aggregated_emotions[emotion] = round(np.mean(values), 3)
        
        return {
            "average_sentiment_score": round(np.mean(sentiment_scores), 3),
            "sentiment_variance": round(np.var(sentiment_scores), 3),
            "dominant_emotion": max(aggregated_emotions, key=aggregated_emotions.get) if aggregated_emotions else None,
            "emotions": aggregated_emotions,
            "total_analyzed": len(results)
        }


# Global instance
_analyzer = None

def get_sentiment_analyzer() -> EnhancedSentimentAnalyzer:
    """Get or create sentiment analyzer"""
    global _analyzer
    if _analyzer is None:
        _analyzer = EnhancedSentimentAnalyzer()
    return _analyzer
