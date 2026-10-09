"""
Data Collection Layer — Scrapers and CSV Ingestors

Since data has already been extracted to output/*.csv, this module provides:
1. CSV ingestors that load existing data into a common schema
2. Scraper stubs for future live data collection (Amazon, News, Social)
3. Common schema normalization
"""
import os
import re
import uuid
import hashlib
import logging
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Common Schema
# ──────────────────────────────────────────────
COMMON_SCHEMA_COLS = [
    "id", "source", "platform", "author", "text", "clean_text",
    "language", "created_at", "product_or_topic", "url", "raw_metadata",
]


def _generate_id(text: str, source: str) -> str:
    """Deterministic ID from content hash for dedup."""
    h = hashlib.sha256(f"{source}:{text}".encode()).hexdigest()[:16]
    return h


# ──────────────────────────────────────────────
# Text Cleaning Pipeline
# ──────────────────────────────────────────────
def clean_text(text: str) -> str:
    """
    Clean raw text:
    - Lowercase
    - Remove URLs, @mentions, #hashtags (keep words)
    - Normalize whitespace
    - Handle emojis (keep them — useful for sentiment)
    """
    if not isinstance(text, str) or not text.strip():
        return ""
    text = text.lower()
    text = re.sub(r"https?://\S+|www\.\S+", "", text)
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"#(\w+)", r"\1", text)  # keep hashtag text, remove #
    text = re.sub(r"<[^>]+>", "", text)     # strip HTML tags
    text = re.sub(r"[\"']", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def deduplicate(df: pd.DataFrame, text_col: str = "text") -> pd.DataFrame:
    """Remove exact-duplicate texts."""
    before = len(df)
    df = df.drop_duplicates(subset=[text_col], keep="first").reset_index(drop=True)
    removed = before - len(df)
    if removed:
        logger.info(f"Dedup: removed {removed} duplicates")
    return df


# ──────────────────────────────────────────────
# CSV Ingestors (load your existing data)
# ──────────────────────────────────────────────
def ingest_reviews_csv(csv_path: str) -> pd.DataFrame:
    """
    Ingest output/results.csv or output/row_keywords_results.csv.
    Schema: category, platform, product_url, original_text, clean_text, sentiment_label, sentiment_score [, row_keywords]
    """
    logger.info(f"Ingesting reviews CSV: {csv_path}")
    df = pd.read_csv(csv_path)

    records = []
    for _, row in df.iterrows():
        text = str(row.get("original_text", ""))
        records.append({
            "id": _generate_id(text, "amazon_review"),
            "source": "amazon_review",
            "platform": str(row.get("platform", "amazon")),
            "author": "",
            "text": text,
            "clean_text": str(row.get("clean_text", clean_text(text))),
            "language": "en",
            "created_at": "",
            "product_or_topic": str(row.get("category", "unknown")),
            "url": str(row.get("product_url", "")),
            "raw_metadata": str({
                "sentiment_label": row.get("sentiment_label"),
                "sentiment_score": row.get("sentiment_score"),
                "row_keywords": row.get("row_keywords", ""),
            }),
        })

    result = pd.DataFrame(records, columns=COMMON_SCHEMA_COLS)
    result = deduplicate(result)
    logger.info(f"Ingested {len(result)} review records")
    return result


def ingest_news_csv(csv_path: str) -> pd.DataFrame:
    """
    Ingest output/news_results.csv.
    Schema: platform, keyword, title, description, sentiment_label, sentiment_score, published_date
    """
    logger.info(f"Ingesting news CSV: {csv_path}")
    df = pd.read_csv(csv_path)

    records = []
    for _, row in df.iterrows():
        title = str(row.get("title", ""))
        desc = str(row.get("description", ""))
        # Strip HTML from news description
        text = re.sub(r"<[^>]+>", "", f"{title} {desc}")
        records.append({
            "id": _generate_id(text, "news"),
            "source": "news",
            "platform": "google_news",
            "author": "",
            "text": text,
            "clean_text": clean_text(text),
            "language": "en",
            "created_at": str(row.get("published_date", "")),
            "product_or_topic": str(row.get("keyword", "general")),
            "url": "",
            "raw_metadata": str({
                "sentiment_label": row.get("sentiment_label"),
                "sentiment_score": row.get("sentiment_score"),
            }),
        })

    result = pd.DataFrame(records, columns=COMMON_SCHEMA_COLS)
    result = deduplicate(result)
    logger.info(f"Ingested {len(result)} news records")
    return result


def ingest_enhanced_sentiment_csv(csv_path: str) -> pd.DataFrame:
    """
    Ingest output/amazon_sentiment_analysis_*.csv (large analyzed dataset).
    Schema: product_category, product_name, source_type, source_name, text, rating, date, ...
    """
    logger.info(f"Ingesting enhanced sentiment CSV: {csv_path}")
    df = pd.read_csv(csv_path)

    records = []
    for _, row in df.iterrows():
        text = str(row.get("text", ""))
        records.append({
            "id": _generate_id(text, str(row.get("source_type", "review"))),
            "source": str(row.get("source_type", "amazon_review")),
            "platform": str(row.get("source_name", "Amazon")),
            "author": "",
            "text": text,
            "clean_text": clean_text(text),
            "language": "en",
            "created_at": str(row.get("date", "")),
            "product_or_topic": str(row.get("product_name", row.get("product_category", "unknown"))),
            "url": "",
            "raw_metadata": str({
                "product_category": row.get("product_category"),
                "rating": row.get("rating"),
                "verified_purchase": row.get("verified_purchase"),
                "sentiment_label": row.get("sentiment_label"),
                "sentiment_score": row.get("sentiment_score"),
            }),
        })

    result = pd.DataFrame(records, columns=COMMON_SCHEMA_COLS)
    result = deduplicate(result)
    logger.info(f"Ingested {len(result)} enhanced records")
    return result


# ──────────────────────────────────────────────
# Social Media Scraper (stub for future use)
# ──────────────────────────────────────────────
def scrape_social_media(query: str, platform: str = "twitter", max_results: int = 100) -> pd.DataFrame:
    """
    Placeholder for social media scraping.
    TODO (Milestone 1): Implement with Twitter/X API v2 or Reddit PRAW.

    Args:
        query: Search query
        platform: Target platform
        max_results: Max records to fetch

    Returns:
        DataFrame in common schema
    """
    logger.warning(f"Social media scraping not yet implemented for {platform}. Returning empty DataFrame.")
    return pd.DataFrame(columns=COMMON_SCHEMA_COLS)


# ──────────────────────────────────────────────
# Review Scraper (wraps existing Selenium scraper)
# ──────────────────────────────────────────────
def scrape_amazon_reviews(product_url: str) -> pd.DataFrame:
    """
    Wrapper around existing Selenium Amazon scraper.
    Normalizes output to common schema.
    """
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
        from scraper.selenium_scraper import scrape_reviews
        raw = scrape_reviews(product_url)
    except ImportError:
        logger.warning("Selenium scraper not available. Install selenium + chromedriver.")
        return pd.DataFrame(columns=COMMON_SCHEMA_COLS)

    records = []
    for item in raw:
        text = item.get("text", "")
        records.append({
            "id": _generate_id(text, "amazon_review"),
            "source": "amazon_review",
            "platform": "amazon",
            "author": item.get("author", ""),
            "text": text,
            "clean_text": clean_text(text),
            "language": "en",
            "created_at": datetime.now().isoformat(),
            "product_or_topic": "",
            "url": product_url,
            "raw_metadata": str(item),
        })

    return pd.DataFrame(records, columns=COMMON_SCHEMA_COLS)


# ──────────────────────────────────────────────
# News Scraper (wraps existing RSS scraper)
# ──────────────────────────────────────────────
def scrape_google_news(keywords: List[str] = None) -> pd.DataFrame:
    """
    Wrapper around existing Google News RSS scraper.
    """
    if keywords is None:
        keywords = ["technology", "amazon", "consumer electronics"]

    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
        from scraper.news_scraper import scrape_news
        raw = scrape_news(keywords)
    except ImportError:
        logger.warning("News scraper not available. Install feedparser.")
        return pd.DataFrame(columns=COMMON_SCHEMA_COLS)

    records = []
    for article in raw:
        text = f"{article.get('title', '')} {article.get('description', '')}"
        records.append({
            "id": _generate_id(text, "news"),
            "source": "news",
            "platform": "google_news",
            "author": "",
            "text": text,
            "clean_text": clean_text(text),
            "language": "en",
            "created_at": article.get("published_date", ""),
            "product_or_topic": article.get("keyword", ""),
            "url": article.get("link", ""),
            "raw_metadata": str(article),
        })

    return pd.DataFrame(records, columns=COMMON_SCHEMA_COLS)
