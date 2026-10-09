"""
Trend Analytics Aggregation Pipeline
=====================================
Reads enriched data and produces aggregated analytics for dashboards and alerts.

Generates:
    - data/analytics/sentiment_trends.parquet   (daily/weekly sentiment by product)
    - data/analytics/topic_trends.parquet        (topic popularity over time)
    - data/analytics/product_comparison.parquet   (cross-product comparisons)
    - data/analytics/summary_stats.json           (headline numbers)

Usage:
    python -m pipelines.analytics_pipeline
"""
import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("analytics_pipeline")

ENRICHED_DIR = os.path.join(PROJECT_ROOT, "data", "enriched")
ANALYTICS_DIR = os.path.join(PROJECT_ROOT, "data", "analytics")


def run_analytics(input_path: str = None) -> dict:
    """
    Generate aggregated analytics from enriched data.

    Returns:
        Summary stats dict
    """
    os.makedirs(ANALYTICS_DIR, exist_ok=True)

    if input_path is None:
        input_path = os.path.join(ENRICHED_DIR, "enriched_latest.parquet")

    if not os.path.exists(input_path):
        logger.error(f"Enriched data not found: {input_path}")
        logger.info("Run: python -m pipelines.sentiment_topic_pipeline")
        return {}

    logger.info(f"Loading enriched data from {input_path}")
    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} records")

    # Parse dates where available
    df["date"] = pd.to_datetime(df["created_at"], errors="coerce")
    has_dates = df["date"].notna().sum()
    logger.info(f"Records with parseable dates: {has_dates}/{len(df)}")

    summary = {}

    # ── 1. Overall Summary Stats ──
    total = len(df)
    pos = (df["sentiment_label"].isin(["positive", "very_positive"])).sum()
    neg = (df["sentiment_label"].isin(["negative", "very_negative"])).sum()
    neu = (df["sentiment_label"] == "neutral").sum()

    summary = {
        "total_records": int(total),
        "positive": int(pos),
        "negative": int(neg),
        "neutral": int(neu),
        "positive_pct": round(pos / max(total, 1) * 100, 1),
        "negative_pct": round(neg / max(total, 1) * 100, 1),
        "mean_sentiment_score": round(float(df["sentiment_score"].mean()), 4),
        "std_sentiment_score": round(float(df["sentiment_score"].std()), 4),
        "unique_products": int(df["product_or_topic"].nunique()),
        "unique_sources": int(df["source"].nunique()),
        "unique_topics": int(df["topic_id"].nunique()),
        "generated_at": datetime.now().isoformat(),
    }

    with open(os.path.join(ANALYTICS_DIR, "summary_stats.json"), "w") as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Summary: {summary}")

    # ── 2. Sentiment Trends by Product ──
    product_groups = df.groupby("product_or_topic").agg(
        count=("sentiment_score", "size"),
        mean_score=("sentiment_score", "mean"),
        std_score=("sentiment_score", "std"),
        pos_count=("sentiment_label", lambda x: x.isin(["positive", "very_positive"]).sum()),
        neg_count=("sentiment_label", lambda x: x.isin(["negative", "very_negative"]).sum()),
    ).reset_index()
    product_groups["pos_pct"] = (product_groups["pos_count"] / product_groups["count"] * 100).round(1)
    product_groups["neg_pct"] = (product_groups["neg_count"] / product_groups["count"] * 100).round(1)

    product_path = os.path.join(ANALYTICS_DIR, "product_comparison.parquet")
    product_groups.to_parquet(product_path, index=False)
    logger.info(f"Product comparison saved: {product_path} ({len(product_groups)} products)")

    # ── 3. Sentiment by Source ──
    source_groups = df.groupby("source").agg(
        count=("sentiment_score", "size"),
        mean_score=("sentiment_score", "mean"),
    ).reset_index()

    source_path = os.path.join(ANALYTICS_DIR, "source_comparison.parquet")
    source_groups.to_parquet(source_path, index=False)

    # ── 4. Topic Trends ──
    topic_groups = df.groupby(["topic_id", "topic_label"]).agg(
        count=("sentiment_score", "size"),
        mean_score=("sentiment_score", "mean"),
    ).reset_index().sort_values("count", ascending=False)

    topic_path = os.path.join(ANALYTICS_DIR, "topic_trends.parquet")
    topic_groups.to_parquet(topic_path, index=False)
    logger.info(f"Topic trends saved: {topic_path} ({len(topic_groups)} topics)")

    # ── 5. Time-series sentiment (if dates available) ──
    if has_dates > 10:
        df_dated = df[df["date"].notna()].copy()
        df_dated["date_day"] = df_dated["date"].dt.date

        daily = df_dated.groupby("date_day").agg(
            count=("sentiment_score", "size"),
            mean_score=("sentiment_score", "mean"),
            pos_count=("sentiment_label", lambda x: x.isin(["positive", "very_positive"]).sum()),
            neg_count=("sentiment_label", lambda x: x.isin(["negative", "very_negative"]).sum()),
        ).reset_index()
        daily["date_day"] = daily["date_day"].astype(str)

        daily_path = os.path.join(ANALYTICS_DIR, "sentiment_trends.parquet")
        daily.to_parquet(daily_path, index=False)
        logger.info(f"Daily sentiment trends saved: {daily_path}")

    # ── 6. Detect anomalies / spikes ──
    if len(product_groups) > 0:
        mean_all = float(df["sentiment_score"].mean())
        std_all = float(df["sentiment_score"].std())
        if std_all > 0:
            product_groups["z_score"] = (product_groups["mean_score"] - mean_all) / std_all
            spikes = product_groups[product_groups["z_score"].abs() > 1.5]
            if len(spikes) > 0:
                logger.info(f"Detected {len(spikes)} products with anomalous sentiment:")
                for _, row in spikes.iterrows():
                    direction = "above" if row["z_score"] > 0 else "below"
                    logger.info(f"  {row['product_or_topic']}: z={row['z_score']:.2f} ({direction} avg)")

    return summary


if __name__ == "__main__":
    run_analytics()
