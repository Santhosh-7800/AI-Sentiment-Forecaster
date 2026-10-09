"""
Keyword Analysis Service
Extracts and analyzes keywords from text using multiple methods
"""
import logging
import re
from typing import Dict, List, Any, Tuple
from collections import Counter
import string

logger = logging.getLogger(__name__)

# Try to import advanced keyword extractors (optional)
try:
    import yake
    YAKE_AVAILABLE = True
except ImportError:
    YAKE_AVAILABLE = False
    logger.warning("YAKE not available. Install with: pip install yake")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available for TF-IDF")


class KeywordAnalyzer:
    """Advanced keyword extraction and analysis"""

    def __init__(self):
        """Initialize keyword analyzer"""
        logger.info("Initializing keyword analyzer...")

        # Common stop words to filter out
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'was', 'are', 'were', 'been', 'be',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which', 'who',
            'when', 'where', 'why', 'how', 'am', 'as', 'if', 'so', 'than', 'such',
            'no', 'not', 'only', 'own', 'same', 'into', 'about', 'just', 'very',
            'up', 'out', 'all', 'more', 'some', 'any', 'my', 'your', 'their'
        }

        # Initialize YAKE if available
        if YAKE_AVAILABLE:
            self.yake_extractor = yake.KeywordExtractor(
                lan="en",
                n=3,  # Max ngram size
                dedupLim=0.7,
                top=20,
                features=None
            )
        else:
            self.yake_extractor = None

        logger.info("[OK] Keyword analyzer initialized")

    def extract_keywords(
        self,
        text: str,
        method: str = "auto",
        max_keywords: int = 10,
        min_word_length: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Extract keywords from text

        Args:
            text: Input text
            method: "auto", "yake", "frequency", "ngram"
            max_keywords: Maximum number of keywords to return
            min_word_length: Minimum word length to consider

        Returns:
            List of keyword dicts with score and text
        """
        if not text or not text.strip():
            return []

        # Clean text
        text = self._clean_text(text)

        # Choose extraction method
        if method == "auto":
            if YAKE_AVAILABLE:
                method = "yake"
            else:
                method = "frequency"

        if method == "yake" and YAKE_AVAILABLE:
            keywords = self._extract_yake(text, max_keywords)
        elif method == "ngram":
            keywords = self._extract_ngrams(text, max_keywords, min_word_length)
        else:
            keywords = self._extract_frequency(text, max_keywords, min_word_length)

        return keywords

    def _extract_yake(self, text: str, max_keywords: int) -> List[Dict[str, Any]]:
        """Extract keywords using YAKE algorithm"""
        try:
            keywords = self.yake_extractor.extract_keywords(text)

            results = []
            for kw, score in keywords[:max_keywords]:
                # YAKE scores are lower for better keywords (inverse)
                # Normalize to 0-1 where 1 is best
                normalized_score = 1 / (1 + score)
                results.append({
                    "keyword": kw,
                    "score": round(normalized_score, 4),
                    "method": "yake"
                })

            return results
        except Exception as e:
            logger.error(f"YAKE extraction error: {e}")
            return self._extract_frequency(text, max_keywords)

    def _extract_frequency(
        self,
        text: str,
        max_keywords: int,
        min_length: int = 3
    ) -> List[Dict[str, Any]]:
        """Extract keywords based on frequency"""
        # Tokenize
        words = re.findall(r'\b[a-z]+\b', text.lower())

        # Filter
        words = [
            w for w in words
            if len(w) >= min_length and w not in self.stop_words
        ]

        # Count
        counter = Counter(words)
        total = sum(counter.values())

        results = []
        for word, count in counter.most_common(max_keywords):
            score = count / total if total > 0 else 0
            results.append({
                "keyword": word,
                "score": round(score, 4),
                "count": count,
                "method": "frequency"
            })

        return results

    def _extract_ngrams(
        self,
        text: str,
        max_keywords: int,
        min_length: int = 3
    ) -> List[Dict[str, Any]]:
        """Extract n-gram keywords (2-3 word phrases)"""
        text_lower = text.lower()

        # Extract bigrams and trigrams
        words = re.findall(r'\b[a-z]+\b', text_lower)
        words = [w for w in words if len(w) >= min_length and w not in self.stop_words]

        ngrams = []

        # Bigrams
        for i in range(len(words) - 1):
            ngrams.append(f"{words[i]} {words[i+1]}")

        # Trigrams
        for i in range(len(words) - 2):
            ngrams.append(f"{words[i]} {words[i+1]} {words[i+2]}")

        # Count
        counter = Counter(ngrams)
        total = sum(counter.values())

        results = []
        for ngram, count in counter.most_common(max_keywords):
            score = count / total if total > 0 else 0
            results.append({
                "keyword": ngram,
                "score": round(score, 4),
                "count": count,
                "method": "ngram"
            })

        return results

    def analyze_keywords_batch(
        self,
        texts: List[str],
        max_keywords: int = 10
    ) -> Dict[str, Any]:
        """
        Analyze keywords across multiple texts

        Args:
            texts: List of texts
            max_keywords: Max keywords to return

        Returns:
            Aggregated keyword analysis
        """
        all_keywords = []

        for text in texts:
            keywords = self.extract_keywords(text, max_keywords=max_keywords)
            all_keywords.extend(keywords)

        # Aggregate by keyword text
        keyword_scores = {}
        for kw in all_keywords:
            key = kw["keyword"]
            if key not in keyword_scores:
                keyword_scores[key] = []
            keyword_scores[key].append(kw["score"])

        # Calculate average scores
        aggregated = []
        for keyword, scores in keyword_scores.items():
            avg_score = sum(scores) / len(scores)
            frequency = len(scores)
            aggregated.append({
                "keyword": keyword,
                "avg_score": round(avg_score, 4),
                "frequency": frequency,
                "total_score": round(avg_score * frequency, 4)
            })

        # Sort by total score (avg * frequency)
        aggregated.sort(key=lambda x: x["total_score"], reverse=True)

        return {
            "top_keywords": aggregated[:max_keywords],
            "total_texts": len(texts),
            "unique_keywords": len(keyword_scores)
        }

    def extract_trending_keywords(
        self,
        texts_with_dates: List[Tuple[str, str]],
        max_keywords: int = 10
    ) -> Dict[str, Any]:
        """
        Extract trending keywords over time

        Args:
            texts_with_dates: List of (text, date_string) tuples
            max_keywords: Max keywords per period

        Returns:
            Trending keywords analysis
        """
        # Group by date
        date_groups = {}
        for text, date in texts_with_dates:
            if date not in date_groups:
                date_groups[date] = []
            date_groups[date].append(text)

        # Extract keywords for each date
        date_keywords = {}
        for date, texts in date_groups.items():
            analysis = self.analyze_keywords_batch(texts, max_keywords)
            date_keywords[date] = analysis["top_keywords"]

        return {
            "periods": date_keywords,
            "total_periods": len(date_groups)
        }

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove URLs
        text = re.sub(r'http\S+|www\S+', '', text)

        # Remove special characters but keep spaces
        text = re.sub(r'[^\w\s]', ' ', text)

        # Remove extra whitespace
        text = ' '.join(text.split())

        return text


# Global instance
_analyzer = None


def get_keyword_analyzer() -> KeywordAnalyzer:
    """Get or create keyword analyzer instance"""
    global _analyzer
    if _analyzer is None:
        _analyzer = KeywordAnalyzer()
    return _analyzer


# Convenience function
def extract_keywords(
    text: str,
    method: str = "auto",
    max_keywords: int = 10
) -> List[Dict[str, Any]]:
    """Quick keyword extraction"""
    analyzer = get_keyword_analyzer()
    return analyzer.extract_keywords(text, method, max_keywords)
