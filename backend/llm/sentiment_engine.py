"""
Lightweight Sentiment Analysis Engine using VADER
No heavy models - fast startup and processing
"""
from __future__ import annotations

import logging
import re

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
except ImportError:  # pragma: no cover - fallback for lightweight environments
    SentimentIntensityAnalyzer = None

logger = logging.getLogger(__name__)

# Fixed order for consistency with previous implementation
LABEL_CLASSES = ["Negative", "Neutral", "Positive"]


class _FallbackSentimentAnalyzer:
    POSITIVE_WORDS = {"amazing", "awesome", "best", "excellent", "fantastic", "good", "great", "love", "perfect", "superb", "works", "fine"}
    NEGATIVE_WORDS = {"awful", "bad", "broke", "broken", "hate", "poor", "terrible", "waste", "worst", "issue", "problem", "fail", "failed"}

    def polarity_scores(self, text: str):
        tokens = re.findall(r"[a-zA-Z']+", text.lower())
        pos_hits = sum(1 for token in tokens if token in self.POSITIVE_WORDS)
        neg_hits = sum(1 for token in tokens if token in self.NEGATIVE_WORDS)
        total = max(1, len(tokens))
        pos_score = min(1.0, pos_hits / total)
        neg_score = min(1.0, neg_hits / total)
        neutral_score = max(0.0, 1.0 - pos_score - neg_score)
        compound = pos_score - neg_score
        return {"neg": round(neg_score, 4), "neu": round(neutral_score, 4), "pos": round(pos_score, 4), "compound": round(max(-1.0, min(1.0, compound)), 4)}


# Initialize VADER analyzer
if SentimentIntensityAnalyzer is None:
    logger.warning("vaderSentiment not installed; using a heuristic fallback.")
    _analyzer = _FallbackSentimentAnalyzer()
else:
    logger.info("Initializing VADER sentiment analyzer...")
    _analyzer = SentimentIntensityAnalyzer()
    logger.info("[OK] VADER sentiment analyzer loaded (lightweight, no model download needed)")


def get_sentiment(text: str) -> dict:
    """
    Run sentiment classification on *text* using VADER and return:

        {
          "label":            "Positive" | "Neutral" | "Negative",
          "confidence_score": float,           # 0.0 – 1.0
          "percentages":      {"Negative": float, "Neutral": float, "Positive": float},
          "one_hot":          {"Negative": int,   "Neutral": int,   "Positive": int},
          "model":            "vader",
        }
    """
    if not text or not text.strip():
        return {
            "label": "Neutral",
            "confidence_score": 0.0,
            "percentages": {"Negative": 0.0, "Neutral": 100.0, "Positive": 0.0},
            "one_hot": {"Negative": 0, "Neutral": 1, "Positive": 0},
            "model": "vader",
        }

    # Get VADER scores
    scores = _analyzer.polarity_scores(text[:512])

    # VADER returns: neg, neu, pos (0-1), compound (-1 to 1)
    neg_pct = scores["neg"] * 100
    neu_pct = scores["neu"] * 100
    pos_pct = scores["pos"] * 100
    compound = scores["compound"]

    # Determine label based on compound score
    # compound > 0.05: Positive, < -0.05: Negative, else: Neutral
    if compound >= 0.05:
        top_label = "Positive"
        confidence = pos_pct / 100
    elif compound <= -0.05:
        top_label = "Negative"
        confidence = neg_pct / 100
    else:
        top_label = "Neutral"
        confidence = neu_pct / 100

    formatted = {
        "Negative": round(neg_pct, 2),
        "Neutral": round(neu_pct, 2),
        "Positive": round(pos_pct, 2),
    }

    return {
        "label": top_label,
        "confidence_score": round(confidence, 4),
        "percentages": formatted,
        "one_hot": {cls: (1 if cls == top_label else 0) for cls in LABEL_CLASSES},
        "model": "vader",
    }
