"""
Groq-based Product and Sentiment Analysis Service
Generates detailed insights using Groq LLM for product analysis and sentiment interpretation
"""

import logging
from typing import Optional, Dict, Any, List
from rag.rag_service import get_llm_model
from rag.config import rag_config

logger = logging.getLogger(__name__)


class GroqAnalysisService:
    """Service for generating AI-powered product and sentiment insights using Groq LLM"""

    def __init__(self):
        """Initialize the Groq analysis service with LLM"""
        try:
            self.llm = get_llm_model()
            logger.info("[OK] Groq analysis service initialized")
        except Exception as e:
            logger.error(f"[FAIL] Failed to initialize Groq: {e}")
            self.llm = None

    def generate_product_insights(
        self,
        product: str,
        sentiment_breakdown: Dict[str, int],
        article_count: int = 0,
        price_sensitivity: Optional[Dict[str, Any]] = None,
        daily_trend: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive product insights using Groq LLM

        Args:
            product: Product name/category
            sentiment_breakdown: Dict with positive, neutral, negative counts
            article_count: Total number of articles analyzed
            price_sensitivity: Price sensitivity analysis data
            daily_trend: Daily sentiment trend data

        Returns:
            Dict with product_overview, sentiment_analysis, and recommendations
        """
        if not self.llm:
            logger.error("Groq not initialized")
            return {
                "product_overview": ["Groq LLM not available"],
                "sentiment_analysis": [],
                "recommendations": []
            }

        try:
            # Build context from sentiment data
            total = article_count or sum(sentiment_breakdown.values())
            pos = sentiment_breakdown.get("positive", 0)
            neu = sentiment_breakdown.get("neutral", 0)
            neg = sentiment_breakdown.get("negative", 0)

            pos_pct = (pos / total * 100) if total > 0 else 0
            neg_pct = (neg / total * 100) if total > 0 else 0
            neu_pct = (neu / total * 100) if total > 0 else 0

            # Build context string
            context = f"""
Product: {product}
Analyzed Data:
- Total mentions/articles: {total}
- Positive mentions: {pos} ({pos_pct:.1f}%)
- Neutral mentions: {neu} ({neu_pct:.1f}%)
- Negative mentions: {neg} ({neg_pct:.1f}%)
"""

            if price_sensitivity:
                psi = price_sensitivity.get("price_sensitivity_index", 0)
                context += f"""
Price Analysis:
- Price positive mentions: {price_sensitivity.get('price_positive_mentions', 0)}
- Price negative mentions: {price_sensitivity.get('price_negative_mentions', 0)}
- Price sensitivity index: {psi:.2f}
"""

            # Generate product overview
            overview_prompt = f"""{context}

Based on the sentiment analysis above, provide 3-4 key observations about {product}:
1. What are the main strengths/positives mentioned?
2. What are the main weaknesses/negatives?
3. Overall market perception and positioning

Format as bullet points. Be specific and factual."""

            overview_message = self.llm.invoke(overview_prompt)
            overview_response = overview_message.content if hasattr(overview_message, 'content') else str(overview_message)
            product_overview = self._parse_bullet_points(overview_response)

            # Generate sentiment analysis
            sentiment_prompt = f"""{context}

Analyze the sentiment patterns for {product}:
1. What factors are driving the positive sentiment?
2. What factors are triggering negative sentiment?
3. Are there any emerging trends in the sentiment data?

Format as bullet points. Focus on root causes and patterns."""

            sentiment_message = self.llm.invoke(sentiment_prompt)
            sentiment_response = sentiment_message.content if hasattr(sentiment_message, 'content') else str(sentiment_message)
            sentiment_analysis = self._parse_bullet_points(sentiment_response)

            # Generate recommendations
            rec_prompt = f"""{context}

Based on this sentiment analysis, provide 3-4 strategic recommendations for {product}:
1. Based on negative feedback, what improvements should be prioritized?
2. Based on positive feedback, what should be emphasized in marketing?
3. What market opportunities exist?

Format as bullet points. Be actionable and specific."""

            rec_message = self.llm.invoke(rec_prompt)
            rec_response = rec_message.content if hasattr(rec_message, 'content') else str(rec_message)
            recommendations = self._parse_bullet_points(rec_response)

            return {
                "product_overview": product_overview,
                "sentiment_analysis": sentiment_analysis,
                "recommendations": recommendations
            }

        except Exception as e:
            logger.error(f"Error generating product insights: {e}")
            return {
                "product_overview": [f"Error: {str(e)}"],
                "sentiment_analysis": [],
                "recommendations": []
            }

    def generate_sentiment_insights(
        self,
        sentiment_breakdown: Dict[str, int],
        category: str = "all products"
    ) -> List[str]:
        """
        Generate insights specifically about sentiment patterns

        Args:
            sentiment_breakdown: Dict with positive, neutral, negative counts
            category: Product category or name

        Returns:
            List of sentiment-specific insights
        """
        if not self.llm:
            return ["Groq LLM not available"]

        try:
            total = sum(sentiment_breakdown.values())
            if total == 0:
                return ["No sentiment data available"]

            pos_pct = (sentiment_breakdown.get("positive", 0) / total * 100)
            neg_pct = (sentiment_breakdown.get("negative", 0) / total * 100)
            neu_pct = (sentiment_breakdown.get("neutral", 0) / total * 100)

            prompt = f"""Analyze this sentiment distribution for {category}:
- Positive: {pos_pct:.1f}%
- Neutral: {neu_pct:.1f}%
- Negative: {neg_pct:.1f}%

Generate 3-4 insights about what this sentiment distribution tells us about {category}.
Consider:
1. Overall customer satisfaction level
2. Sentiment distribution balance
3. Confidence level in the analysis

Format as a bullet list."""

            response_message = self.llm.invoke(prompt)
            response = response_message.content if hasattr(response_message, 'content') else str(response_message)
            return self._parse_bullet_points(response)

        except Exception as e:
            logger.error(f"Error generating sentiment insights: {e}")
            return [f"Error analyzing sentiment: {str(e)}"]

    def _parse_bullet_points(self, text: str) -> List[str]:
        """
        Parse LLM response into clean bullet points

        Args:
            text: LLM response text

        Returns:
            List of cleaned bullet points
        """
        if not text:
            return []

        lines = text.split('\n')
        points = []

        for line in lines:
            line = line.strip()
            # Remove common bullet point markers
            if line and not line.isspace():
                # Remove bullet markers (-, *, •, 1., 2., etc.)
                cleaned = line
                for marker in ['-', '*', '•', '·']:
                    if cleaned.startswith(marker):
                        cleaned = cleaned[len(marker):].strip()
                        break

                # Remove numbering (1., 2., etc.)
                import re
                cleaned = re.sub(r'^\d+\.\s*', '', cleaned)

                # Remove markdown ** bold markers
                cleaned = cleaned.replace('**', '')

                if cleaned and len(cleaned) > 5:  # Skip very short lines
                    points.append(cleaned)

        return points[:5]  # Return max 5 points


# Global instance
_analysis_service: Optional[GroqAnalysisService] = None


def get_analysis_service() -> GroqAnalysisService:
    """Get or create the analysis service instance"""
    global _analysis_service
    if _analysis_service is None:
        _analysis_service = GroqAnalysisService()
    return _analysis_service
