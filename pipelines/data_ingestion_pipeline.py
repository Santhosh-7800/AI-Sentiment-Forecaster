"""
Data Ingestion Pipeline
=======================
Orchestrates: CSV ingest → clean → normalize → validate → save to data/processed/

Usage:
    python -m pipelines.data_ingestion_pipeline
    python -m pipelines.data_ingestion_pipeline --source reviews --csv output/results.csv
"""
import os
import sys
import glob
import logging
import argparse
import pandas as pd
from datetime import datetime

# Ensure project root is on path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from data_collection.collectors import (
    ingest_reviews_csv,
    ingest_news_csv,
    ingest_enhanced_sentiment_csv,
    clean_text,
    deduplicate,
    COMMON_SCHEMA_COLS,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("data_ingestion")

PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")


def validate_schema(df: pd.DataFrame) -> bool:
    """Validate that DataFrame has all common schema columns."""
    missing = set(COMMON_SCHEMA_COLS) - set(df.columns)
    if missing:
        logger.error(f"Schema validation failed. Missing columns: {missing}")
        return False
    return True


def log_stats(df: pd.DataFrame, label: str) -> None:
    """Log basic statistics about the ingested data."""
    logger.info(f"--- {label} Stats ---")
    logger.info(f"  Total records: {len(df)}")
    logger.info(f"  Sources: {df['source'].value_counts().to_dict()}")
    logger.info(f"  Platforms: {df['platform'].value_counts().to_dict()}")
    logger.info(f"  Products/Topics: {df['product_or_topic'].nunique()} unique")
    empty_text = (df["clean_text"].str.strip() == "").sum()
    if empty_text:
        logger.warning(f"  Empty clean_text: {empty_text} records")


def run_full_ingestion() -> pd.DataFrame:
    """
    Run the full data ingestion pipeline over all CSVs in output/.
    Returns combined DataFrame saved to data/processed/all_data.parquet.
    """
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    all_frames = []

    # 1. Ingest product reviews (results.csv, row_keywords_results.csv)
    for pattern in ["output/results.csv", "output/row_keywords_results.csv"]:
        csv_path = os.path.join(PROJECT_ROOT, pattern)
        if os.path.exists(csv_path):
            df = ingest_reviews_csv(csv_path)
            all_frames.append(df)

    # 2. Ingest news
    news_path = os.path.join(PROJECT_ROOT, "output", "news_results.csv")
    if os.path.exists(news_path):
        df = ingest_news_csv(news_path)
        all_frames.append(df)

    # 3. Ingest enhanced sentiment CSVs (amazon_sentiment_analysis_*.csv)
    for csv_path in glob.glob(os.path.join(PROJECT_ROOT, "output", "amazon_sentiment_analysis_*.csv")):
        df = ingest_enhanced_sentiment_csv(csv_path)
        all_frames.append(df)

    # 4. Ingest sentiment_results CSVs
    for csv_path in glob.glob(os.path.join(PROJECT_ROOT, "output", "sentiment_results_*.csv")):
        try:
            df = ingest_enhanced_sentiment_csv(csv_path)
            all_frames.append(df)
        except Exception as e:
            logger.warning(f"Skipped {csv_path}: {e}")

    if not all_frames:
        logger.error("No CSV files found in output/. Nothing to ingest.")
        return pd.DataFrame(columns=COMMON_SCHEMA_COLS)

    # Combine and deduplicate globally
    combined = pd.concat(all_frames, ignore_index=True)
    combined = deduplicate(combined)

    # Validate
    if not validate_schema(combined):
        logger.error("Schema validation failed on combined data!")
        return combined

    log_stats(combined, "Combined Ingestion")

    # Save
    out_path = os.path.join(PROCESSED_DIR, "all_data.parquet")
    combined.to_parquet(out_path, index=False, engine="pyarrow")
    logger.info(f"Saved {len(combined)} records to {out_path}")

    # Also save per-source splits
    for source in combined["source"].unique():
        subset = combined[combined["source"] == source]
        source_path = os.path.join(PROCESSED_DIR, f"{source}.parquet")
        subset.to_parquet(source_path, index=False, engine="pyarrow")
        logger.info(f"Saved {len(subset)} {source} records to {source_path}")

    return combined


def run_single_ingestion(source_type: str, csv_path: str) -> pd.DataFrame:
    """Ingest a single CSV file."""
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    ingestors = {
        "reviews": ingest_reviews_csv,
        "news": ingest_news_csv,
        "enhanced": ingest_enhanced_sentiment_csv,
    }

    ingestor = ingestors.get(source_type)
    if not ingestor:
        logger.error(f"Unknown source type: {source_type}. Use: {list(ingestors.keys())}")
        return pd.DataFrame(columns=COMMON_SCHEMA_COLS)

    df = ingestor(csv_path)

    if validate_schema(df):
        log_stats(df, source_type)
        out_path = os.path.join(PROCESSED_DIR, f"{source_type}_{datetime.now().strftime('%Y%m%d')}.parquet")
        df.to_parquet(out_path, index=False, engine="pyarrow")
        logger.info(f"Saved to {out_path}")

    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TrendAI Data Ingestion Pipeline")
    parser.add_argument("--source", choices=["reviews", "news", "enhanced", "all"], default="all",
                        help="Source type to ingest")
    parser.add_argument("--csv", type=str, default=None, help="Path to specific CSV file")
    args = parser.parse_args()

    if args.source == "all":
        run_full_ingestion()
    else:
        if not args.csv:
            print("Error: --csv path required when --source is not 'all'")
            sys.exit(1)
        run_single_ingestion(args.source, args.csv)
