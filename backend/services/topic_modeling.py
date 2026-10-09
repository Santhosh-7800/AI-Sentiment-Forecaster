"""
Topic Modeling Service - Extract emerging topics and trends from reviews
Uses BERTopic for dynamic topic modeling
"""
import logging
from typing import Dict, List, Any
from collections import defaultdict
import numpy as np
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class TopicModelingService:
    """Extract and track topics from product reviews"""
    
    def __init__(self):
        """Initialize topic modeling with pre-trained embeddings"""
        logger.info("Loading topic modeling models...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.topic_model = None
        self.topics_cache = {}
        logger.info("Topic modeling service initialized")
    
    def train_topics(self, texts: List[str], product: str, min_topic_size: int = 3) -> Dict[str, Any]:
        """
        Train BERTopic on given texts to extract topics
        
        Args:
            texts: List of review texts
            product: Product name for caching
            min_topic_size: Minimum documents per topic
        
        Returns:
            Dictionary with topics, their keywords, and distributions
        """
        try:
            if not texts or len(texts) < min_topic_size:
                logger.warning(f"Insufficient texts for topic modeling: {len(texts)}")
                return self._empty_topics_response()
            
            logger.info(f"Training topic model on {len(texts)} texts for {product}...")
            
            # Create embeddings
            embeddings = self.embedding_model.encode(texts, show_progress_bar=False)
            
            # Train BERTopic
            self.topic_model = BERTopic(
                embedding_model=self.embedding_model,
                min_topic_size=max(min_topic_size, 2),
                language="english",
                calculate_probabilities=True,
                verbose=False
            )
            
            topics, probabilities = self.topic_model.fit_transform(texts, embeddings)
            
            # Extract topic information
            topic_info = self._extract_topic_details(texts, topics, probabilities)
            
            # Cache results
            self.topics_cache[product] = topic_info
            logger.info(f"Extracted {len(topic_info['topics'])} topics from {product}")
            
            return topic_info
            
        except Exception as e:
            logger.error(f"Topic modeling error: {str(e)}")
            return self._empty_topics_response()
    
    def _extract_topic_details(self, texts: List[str], topics: List[int], 
                               probabilities: np.ndarray) -> Dict[str, Any]:
        """Extract detailed topic information"""
        try:
            topic_details = []
            topic_keywords = self.topic_model.get_topics()
            
            # Build topic summaries
            for topic_id in sorted(set(topics)):
                if topic_id == -1:  # Outliers
                    continue
                
                # Get documents for this topic
                topic_docs = [texts[i] for i, t in enumerate(topics) if t == topic_id]
                topic_probs = probabilities[topics == topic_id].mean(axis=0)
                
                # Get keywords
                keywords = topic_keywords.get(topic_id, [])
                keyword_list = [kw.split("*")[0] for kw, _ in keywords[:5]]
                
                # Calculate topic strength
                topic_strength = float(np.mean([p[topic_id] if topic_id < len(p) else 0 
                                               for p in probabilities[topics == topic_id]]))
                
                topic_details.append({
                    "topic_id": int(topic_id),
                    "name": f"Topic {topic_id}: {' | '.join(keyword_list[:3])}",
                    "keywords": keyword_list,
                    "doc_count": len(topic_docs),
                    "strength": round(topic_strength, 4),
                    "sample_docs": topic_docs[:2],  # 2 representative documents
                    "percentage": round((len(topic_docs) / len(texts)) * 100, 2)
                })
            
            # Sort by strength
            topic_details.sort(key=lambda x: x['strength'], reverse=True)
            
            return {
                "topics": topic_details[:5],  # Top 5 topics
                "total_unique_topics": len(set(topics)) - (1 if -1 in set(topics) else 0),
                "outlier_percentage": round((list(topics).count(-1) / len(texts)) * 100, 2) if -1 in topics else 0,
                "coverage": round((len(set(topics)) - (1 if -1 in set(topics) else 0)) / len(set(topics)), 4) if set(topics) else 0
            }
        except Exception as e:
            logger.error(f"Error extracting topic details: {str(e)}")
            return self._empty_topics_response()
    
    def _empty_topics_response(self) -> Dict[str, Any]:
        """Return empty topics response"""
        return {
            "topics": [],
            "total_unique_topics": 0,
            "outlier_percentage": 0,
            "coverage": 0
        }
    
    def analyze_topic_evolution(self, texts: List[str], dates: List[str]) -> Dict[str, Any]:
        """
        Analyze how topics evolve over time
        
        Args:
            texts: Review texts
            dates: Corresponding dates
        
        Returns:
            Topic evolution trends
        """
        try:
            logger.info("Analyzing topic evolution...")
            
            if not texts or len(texts) < 3:
                return {"evolution": [], "trend": "insufficient_data"}
            
            # Group by time periods
            from datetime import datetime
            time_buckets = defaultdict(list)
            
            for text, date_str in zip(texts, dates):
                try:
                    date_obj = datetime.fromisoformat(date_str) if isinstance(date_str, str) else date_str
                    bucket = date_obj.strftime("%Y-%m")
                except:
                    bucket = "unknown"
                time_buckets[bucket].append(text)
            
            # Analyze topics per time period
            evolution = []
            for period in sorted(time_buckets.keys()):
                period_texts = time_buckets[period]
                if len(period_texts) >= 2:
                    period_topics = self.train_topics(period_texts, f"{period}")
                    evolution.append({
                        "period": period,
                        "topics": period_topics["topics"][:3],
                        "doc_count": len(period_texts)
                    })
            
            return {
                "evolution": evolution[-6:],  # Last 6 periods
                "trend": self._determine_trend(evolution),
                "insight": self._create_evolution_insight(evolution)
            }
        except Exception as e:
            logger.error(f"Topic evolution error: {str(e)}")
            return {"evolution": [], "trend": "error", "insight": ""}
    
    def _determine_trend(self, evolution: List[Dict]) -> str:
        """Determine topic diversity trend"""
        if len(evolution) < 2:
            return "stable"
        
        topic_counts = [len(e.get("topics", [])) for e in evolution[-3:]]
        if not topic_counts:
            return "stable"
        
        recent_avg = np.mean(topic_counts[-2:]) if len(topic_counts) >= 2 else topic_counts[-1]
        earlier_avg = np.mean(topic_counts[:-1]) if len(topic_counts) > 1 else topic_counts[0]
        
        if recent_avg > earlier_avg * 1.2:
            return "increasing"
        elif recent_avg < earlier_avg * 0.8:
            return "decreasing"
        else:
            return "stable"
    
    def _create_evolution_insight(self, evolution: List[Dict]) -> str:
        """Create human-readable insight about topic evolution"""
        if not evolution:
            return "Insufficient data for trend analysis"
        
        if len(evolution) >= 2:
            latest = evolution[-1]
            prev = evolution[-2]
            
            latest_topics = set(t["name"] for t in latest.get("topics", []))
            prev_topics = set(t["name"] for t in prev.get("topics", []))
            
            new_topics = latest_topics - prev_topics
            if new_topics:
                return f"Emerging topics detected: {', '.join(list(new_topics)[:2])}"
        
        return f"Analysis based on {len(evolution)} time periods"


# Global instance
topic_service = None

def get_topic_service() -> TopicModelingService:
    """Get or create topic modeling service"""
    global topic_service
    if topic_service is None:
        topic_service = TopicModelingService()
    return topic_service
