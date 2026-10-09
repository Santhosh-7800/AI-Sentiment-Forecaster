"""
Model Evaluation Script
========================
Milestone 2: Basic metrics and sanity checks for sentiment and topic models.

Usage:
    python -m evaluation.evaluate_models
    python -m evaluation.evaluate_models --data data/enriched/enriched_latest.parquet
"""
import os
import sys
import logging
import argparse
from collections import Counter

import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("evaluate_models")


def evaluate_sentiment(df: pd.DataFrame) -> dict:
    """
    Evaluate sentiment model outputs.
    Since we don't have ground-truth labels, we use distribution checks
    and consistency metrics as sanity checks.
    """
    logger.info("=== Sentiment Model Evaluation ===")
    results = {}

    # 1. Label distribution (should not be heavily skewed to one class)
    label_counts = df["sentiment_label"].value_counts().to_dict()
    results["label_distribution"] = label_counts
    logger.info(f"Label distribution: {label_counts}")

    total = len(df)
    for label, count in label_counts.items():
        pct = count / total * 100
        if pct > 80:
            logger.warning(f"  Skewed: {label} has {pct:.1f}% of all records")

    # 2. Score distribution stats
    scores = df["sentiment_score"].dropna()
    results["score_stats"] = {
        "mean": round(float(scores.mean()), 4),
        "std": round(float(scores.std()), 4),
        "min": round(float(scores.min()), 4),
        "max": round(float(scores.max()), 4),
        "median": round(float(scores.median()), 4),
    }
    logger.info(f"Score stats: {results['score_stats']}")

    # 3. Label-score consistency check
    # Positive labels should have positive scores, negative should have negative
    if "sentiment_label" in df.columns and "sentiment_score" in df.columns:
        pos_mask = df["sentiment_label"].isin(["positive", "very_positive"])
        neg_mask = df["sentiment_label"].isin(["negative", "very_negative"])

        pos_scores = df.loc[pos_mask, "sentiment_score"]
        neg_scores = df.loc[neg_mask, "sentiment_score"]

        pos_consistent = (pos_scores > 0).sum() / max(len(pos_scores), 1)
        neg_consistent = (neg_scores < 0).sum() / max(len(neg_scores), 1)

        results["consistency"] = {
            "positive_label_positive_score": round(pos_consistent, 3),
            "negative_label_negative_score": round(neg_consistent, 3),
        }
        logger.info(f"Consistency: {results['consistency']}")

        if pos_consistent < 0.8:
            logger.warning("  Low positive consistency — investigate label assignment")
        if neg_consistent < 0.8:
            logger.warning("  Low negative consistency — investigate label assignment")

    # 4. Confidence distribution
    if "sentiment_confidence" in df.columns:
        conf = df["sentiment_confidence"].dropna()
        results["confidence_stats"] = {
            "mean": round(float(conf.mean()), 4),
            "low_confidence_pct": round((conf < 0.5).sum() / max(len(conf), 1) * 100, 1),
        }
        logger.info(f"Confidence stats: {results['confidence_stats']}")

    return results


def evaluate_topics(df: pd.DataFrame) -> dict:
    """Evaluate topic model outputs."""
    logger.info("\n=== Topic Model Evaluation ===")
    results = {}

    if "topic_id" not in df.columns:
        logger.warning("No topic_id column found")
        return results

    # 1. Number of topics
    n_topics = df["topic_id"].nunique()
    results["num_topics"] = n_topics
    logger.info(f"Number of unique topics: {n_topics}")

    # 2. Topic distribution
    topic_counts = df["topic_id"].value_counts().head(15).to_dict()
    results["top_topics"] = topic_counts
    logger.info(f"Top topics by count: {topic_counts}")

    # 3. Unassigned documents
    unassigned = (df["topic_id"] == -1).sum()
    unassigned_pct = unassigned / max(len(df), 1) * 100
    results["unassigned_pct"] = round(unassigned_pct, 1)
    logger.info(f"Unassigned documents: {unassigned} ({unassigned_pct:.1f}%)")
    if unassigned_pct > 30:
        logger.warning("  High unassigned rate — consider lowering topic granularity")

    # 4. Topic-sentiment correlation
    if "sentiment_score" in df.columns:
        topic_sentiment = df.groupby("topic_id")["sentiment_score"].agg(["mean", "count"]).reset_index()
        topic_sentiment = topic_sentiment[topic_sentiment["topic_id"] != -1]
        topic_sentiment = topic_sentiment.sort_values("count", ascending=False).head(10)
        results["topic_sentiment"] = topic_sentiment.to_dict("records")
        logger.info("Topic-sentiment correlation (top 10):")
        for _, row in topic_sentiment.iterrows():
            logger.info(f"  Topic {int(row['topic_id'])}: mean={row['mean']:.3f}, n={int(row['count'])}")

    return results


def run_evaluation(data_path: str = None):
    """Run full evaluation suite."""
    if data_path is None:
        data_path = os.path.join(PROJECT_ROOT, "data", "enriched", "enriched_latest.parquet")

    if not os.path.exists(data_path):
        logger.error(f"Data not found: {data_path}")
        logger.info("Run the enrichment pipeline first: python -m pipelines.sentiment_topic_pipeline")
        return

    df = pd.read_parquet(data_path)
    logger.info(f"Loaded {len(df)} records from {data_path}\n")

    sent_results = evaluate_sentiment(df)
    topic_results = evaluate_topics(df)

    logger.info("\n=== EVALUATION SUMMARY ===")
    logger.info(f"Total records evaluated: {len(df)}")
    logger.info(f"Sentiment labels: {sent_results.get('label_distribution', {})}")
    logger.info(f"Score mean: {sent_results.get('score_stats', {}).get('mean', 'N/A')}")
    if sent_results.get("consistency"):
        logger.info(f"Label-score consistency: {sent_results['consistency']}")
    logger.info(f"Topics found: {topic_results.get('num_topics', 'N/A')}")
    logger.info(f"Unassigned docs: {topic_results.get('unassigned_pct', 'N/A')}%")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate sentiment and topic models")
    parser.add_argument("--data", type=str, default=None, help="Path to enriched parquet")
    args = parser.parse_args()
    run_evaluation(args.data)
