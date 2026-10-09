"""
Sentiment & Topic Enrichment Pipeline
======================================
Loads cleaned data from data/processed/, runs sentiment + topic models,
and saves enriched records to data/enriched/.

Usage:
    python -m pipelines.sentiment_topic_pipeline
    python -m pipelines.sentiment_topic_pipeline --input data/processed/all_data.parquet
"""
import os
import sys
import logging
import argparse
import pandas as pd
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from models.sentiment_model import get_sentiment_model
from models.topic_model import get_topic_model

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("sentiment_topic_pipeline")

PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
ENRICHED_DIR = os.path.join(PROJECT_ROOT, "data", "enriched")


def enrich_data(
    input_path: str = None,
    sentiment_batch_size: int = 32,
    topic_method: str = "keybert",
) -> pd.DataFrame:
    """
    Enrich processed data with sentiment scores and topic labels.

    Args:
        input_path: Path to parquet/csv. Defaults to data/processed/all_data.parquet
        sentiment_batch_size: Batch size for sentiment model
        topic_method: 'keybert' or 'bertopic'

    Returns:
        Enriched DataFrame
    """
    os.makedirs(ENRICHED_DIR, exist_ok=True)

    # Load data
    if input_path is None:
        input_path = os.path.join(PROCESSED_DIR, "all_data.parquet")

    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        logger.info("Run the data ingestion pipeline first: python -m pipelines.data_ingestion_pipeline")
        return pd.DataFrame()

    logger.info(f"Loading data from {input_path}")
    if input_path.endswith(".parquet"):
        df = pd.read_parquet(input_path)
    else:
        df = pd.read_csv(input_path)

    logger.info(f"Loaded {len(df)} records")

    # ── Sentiment Analysis ──
    logger.info("Running sentiment analysis...")
    sentiment_model = get_sentiment_model()
    texts = df["clean_text"].fillna("").tolist()
    sentiment_results = sentiment_model.analyze_batch(texts, batch_size=sentiment_batch_size)

    df["sentiment_label"] = [r["sentiment_label"] for r in sentiment_results]
    df["sentiment_score"] = [r["sentiment_score"] for r in sentiment_results]
    df["sentiment_confidence"] = [r["confidence"] for r in sentiment_results]
    df["sentiment_neg"] = [r["scores"].get("negative", 0) for r in sentiment_results]
    df["sentiment_neu"] = [r["scores"].get("neutral", 0) for r in sentiment_results]
    df["sentiment_pos"] = [r["scores"].get("positive", 0) for r in sentiment_results]

    logger.info("Sentiment analysis complete.")
    logger.info(f"  Label distribution: {df['sentiment_label'].value_counts().to_dict()}")

    # ── Topic Modeling ──
    logger.info("Running topic extraction...")
    topic_model = get_topic_model(method=topic_method)
    topic_results = topic_model.extract_topics_batch(texts)

    # Map topic assignments to DataFrame
    doc_topics = topic_results["document_topics"]
    topic_ids = []
    topic_labels = []
    topic_keywords = []

    # Build topic_id -> label mapping
    topic_label_map = {t["topic_id"]: t["topic_label"] for t in topic_results["topics"]}

    for dt in doc_topics:
        tid = dt["topic_id"]
        topic_ids.append(tid)
        topic_labels.append(topic_label_map.get(tid, "unknown"))
        topic_keywords.append(", ".join(dt["keywords"][:5]))

    df["topic_id"] = topic_ids
    df["topic_label"] = topic_labels
    df["keywords"] = topic_keywords

    logger.info(f"Topic extraction complete. Found {len(topic_results['topics'])} topics.")
    for t in topic_results["topics"][:5]:
        logger.info(f"  Topic {t['topic_id']}: {t['topic_label']} (n={t['count']})")

    # ── Save Enriched Data ──
    timestamp = datetime.now().strftime("%Y%m%d")
    out_path = os.path.join(ENRICHED_DIR, f"enriched_data_{timestamp}.parquet")
    df.to_parquet(out_path, index=False, engine="pyarrow")
    logger.info(f"Saved enriched data: {out_path} ({len(df)} records)")

    # Also save latest copy
    latest_path = os.path.join(ENRICHED_DIR, "enriched_latest.parquet")
    df.to_parquet(latest_path, index=False, engine="pyarrow")

    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TrendAI Sentiment & Topic Enrichment Pipeline")
    parser.add_argument("--input", type=str, default=None, help="Input parquet/csv path")
    parser.add_argument("--batch-size", type=int, default=32, help="Sentiment batch size")
    parser.add_argument("--topic-method", choices=["keybert", "bertopic"], default="keybert")
    args = parser.parse_args()

    enrich_data(
        input_path=args.input,
        sentiment_batch_size=args.batch_size,
        topic_method=args.topic_method,
    )
