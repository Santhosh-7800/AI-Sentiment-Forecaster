"""
Sentiment Model — Clean abstraction layer
==========================================
Uses VADER (lightweight) for sentiment analysis instead of heavy transformers.

Produces:
    - sentiment_label: very_negative | negative | neutral | positive | very_positive
    - sentiment_score: float in range [-1.0, 1.0]
"""
import os
import re
import sys
import time
import logging
from typing import Dict, List, Any

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
except ImportError:  # pragma: no cover - fallback for lightweight environments
    SentimentIntensityAnalyzer = None

logger = logging.getLogger(__name__)

FIVE_CLASS_LABELS = ["very_negative", "negative", "neutral", "positive", "very_positive"]


class _FallbackSentimentAnalyzer:
    """Simple heuristic sentiment analyzer used when vaderSentiment is unavailable."""

    POSITIVE_WORDS = {
        "amazing", "awesome", "best", "excellent", "fantastic", "good", "great",
        "happy", "love", "perfect", "positive", "superb", "strong", "works", "fine",
        "excellent", "outstanding", "quality", "satisfied", "impressed", "reliable"
    }
    NEGATIVE_WORDS = {
        "awful", "bad", "broke", "broken", "cheap", "crash", "dissatisfied",
        "hate", "issue", "poor", "terrible", "terribly", "useless", "waste",
        "worst", "problem", "fail", "failed", "slow", "weak"
    }
    NEGATORS = {"not", "never", "no", "none", "hardly"}
    INTENSIFIERS = {"very", "super", "extremely", "really", "so"}

    @staticmethod
    def _tokenize(text: str):
        return re.findall(r"[a-zA-Z']+", text.lower())

    def polarity_scores(self, text: str):
        tokens = self._tokenize(text)
        if not tokens:
            return {"neg": 0.0, "neu": 1.0, "pos": 0.0, "compound": 0.0}

        pos_hits = 0
        neg_hits = 0
        for idx, token in enumerate(tokens):
            if token in self.NEGATORS:
                continue
            if token in self.POSITIVE_WORDS:
                pos_hits += 2
                if idx > 0 and tokens[idx - 1] in self.INTENSIFIERS:
                    pos_hits += 1
            if token in self.NEGATIVE_WORDS:
                neg_hits += 2
                if idx > 0 and tokens[idx - 1] in self.INTENSIFIERS:
                    neg_hits += 1

        total = max(1, len(tokens))
        pos_score = min(1.0, pos_hits / total)
        neg_score = min(1.0, neg_hits / total)
        if "!" in text:
            pos_score = min(1.0, pos_score + 0.1)
            neg_score = min(1.0, neg_score + 0.1)

        neutral_score = max(0.0, 1.0 - pos_score - neg_score)
        compound = pos_score - neg_score
        compound = max(-1.0, min(1.0, round(compound, 4)))
        return {
            "neg": round(max(0.0, neg_score), 4),
            "neu": round(max(0.0, neutral_score), 4),
            "pos": round(max(0.0, pos_score), 4),
            "compound": compound,
        }


def _score_to_five_class(score: float) -> str:
    """Map a [-1, 1] score to five-class label."""
    if score <= -0.6:
        return "very_negative"
    elif score <= -0.2:
        return "negative"
    elif score <= 0.2:
        return "neutral"
    elif score <= 0.6:
        return "positive"
    else:
        return "very_positive"


class SentimentModel:
    """
    Unified sentiment model using VADER (lightweight, no model downloads)
    """

    def __init__(self, use_llm: bool = False):
        self.use_llm = use_llm
        self._analyzer = None
        self._llm_client = None

    def _load_vader(self):
        """Lazy-load the VADER sentiment analyzer."""
        if self._analyzer is None:
            if SentimentIntensityAnalyzer is None:
                logger.warning("vaderSentiment not installed; using heuristic fallback analyzer.")
                self._analyzer = _FallbackSentimentAnalyzer()
            else:
                logger.info("Loading VADER sentiment analyzer...")
                self._analyzer = SentimentIntensityAnalyzer()
                logger.info("[OK] VADER analyzer loaded.")

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of a single text.

        Returns:
            {
                "sentiment_label": str,
                "sentiment_score": float,  # -1.0 to 1.0
                "confidence": float,
                "scores": {"negative": float, "neutral": float, "positive": float}
            }
        """
        if not text or not text.strip():
            return {
                "sentiment_label": "neutral",
                "sentiment_score": 0.0,
                "confidence": 0.0,
                "scores": {"negative": 0.0, "neutral": 1.0, "positive": 0.0},
            }

        self._load_vader()
        start = time.time()

        try:
            # Get VADER scores
            vader_scores = self._analyzer.polarity_scores(text[:512])

            # Extract scores
            neg = vader_scores["neg"]
            neu = vader_scores["neu"]
            pos = vader_scores["pos"]
            compound = vader_scores["compound"]

            scores = {
                "negative": neg,
                "neutral": neu,
                "positive": pos
            }

            label = _score_to_five_class(compound)
            confidence = max(neg, neu, pos)

            latency = time.time() - start
            logger.debug(f"Sentiment analyzed in {latency:.3f}s: {label} ({compound:.3f})")

            return {
                "sentiment_label": label,
                "sentiment_score": round(compound, 4),
                "confidence": round(confidence, 4),
                "scores": {k: round(v, 4) for k, v in scores.items()},
            }
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return {
                "sentiment_label": "neutral",
                "sentiment_score": 0.0,
                "confidence": 0.0,
                "scores": {"negative": 0.0, "neutral": 1.0, "positive": 0.0},
            }

    def analyze_batch(self, texts: List[str], batch_size: int = 32) -> List[Dict[str, Any]]:
        """
        Batch sentiment analysis.

        Args:
            texts: List of text strings
            batch_size: Processing batch size

        Returns:
            List of sentiment result dicts
        """
        results = []
        total = len(texts)
        start = time.time()

        for i in range(0, total, batch_size):
            batch = texts[i : i + batch_size]
            for text in batch:
                results.append(self.analyze(text))
            logger.info(f"Batch progress: {min(i + batch_size, total)}/{total}")

        latency = time.time() - start
        logger.info(f"Batch analysis complete: {total} texts in {latency:.2f}s ({latency/max(total,1):.3f}s/text)")
        return results


# Module-level singleton
_model = None


def get_sentiment_model(use_llm: bool = False) -> SentimentModel:
    """Get or create sentiment model singleton."""
    global _model
    if _model is None:
        _model = SentimentModel(use_llm=use_llm)
    return _model
