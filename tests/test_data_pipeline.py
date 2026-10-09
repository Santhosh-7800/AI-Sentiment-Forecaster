"""
Tests for Data Ingestion Pipeline
==================================
Milestone 1: Basic unit tests for data pipeline.

Run:
    pytest tests/test_data_pipeline.py -v
"""
import os
import sys
import tempfile
import pandas as pd
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from data_collection.collectors import (
    clean_text,
    deduplicate,
    ingest_reviews_csv,
    ingest_news_csv,
    COMMON_SCHEMA_COLS,
)


class TestCleanText:
    """Tests for text cleaning pipeline."""

    def test_removes_urls(self):
        text = "Check this out https://example.com and http://test.org/path"
        result = clean_text(text)
        assert "https://" not in result
        assert "http://" not in result

    def test_removes_mentions(self):
        text = "Hey @user123 look at this"
        result = clean_text(text)
        assert "@user123" not in result

    def test_keeps_hashtag_text(self):
        text = "Love this #ProductReview"
        result = clean_text(text)
        assert "productreview" in result
        assert "#" not in result

    def test_lowercases(self):
        text = "Great PRODUCT Very Good"
        result = clean_text(text)
        assert result == "great product very good"

    def test_strips_html(self):
        text = '<a href="url">Link Text</a> is great'
        result = clean_text(text)
        assert "<a" not in result
        assert "link text" in result

    def test_handles_empty(self):
        assert clean_text("") == ""
        assert clean_text("   ") == ""
        assert clean_text(None) == ""


class TestDeduplication:
    """Tests for deduplication."""

    def test_removes_exact_duplicates(self):
        df = pd.DataFrame({"text": ["hello", "hello", "world"], "other": [1, 2, 3]})
        result = deduplicate(df, text_col="text")
        assert len(result) == 2

    def test_keeps_unique(self):
        df = pd.DataFrame({"text": ["a", "b", "c"]})
        result = deduplicate(df, text_col="text")
        assert len(result) == 3


class TestCSVIngestion:
    """Tests for CSV ingestors."""

    def test_ingest_reviews_csv_schema(self):
        """Test that reviews CSV produces correct schema."""
        csv_path = os.path.join(PROJECT_ROOT, "output", "results.csv")
        if not os.path.exists(csv_path):
            pytest.skip("output/results.csv not found")

        df = ingest_reviews_csv(csv_path)
        assert len(df) > 0
        for col in COMMON_SCHEMA_COLS:
            assert col in df.columns, f"Missing column: {col}"
        assert df["source"].iloc[0] == "amazon_review"

    def test_ingest_news_csv_schema(self):
        """Test that news CSV produces correct schema."""
        csv_path = os.path.join(PROJECT_ROOT, "output", "news_results.csv")
        if not os.path.exists(csv_path):
            pytest.skip("output/news_results.csv not found")

        df = ingest_news_csv(csv_path)
        assert len(df) > 0
        for col in COMMON_SCHEMA_COLS:
            assert col in df.columns, f"Missing column: {col}"
        assert df["source"].iloc[0] == "news"

    def test_ingest_creates_unique_ids(self):
        """Test that IDs are deterministic and unique per text."""
        csv_path = os.path.join(PROJECT_ROOT, "output", "results.csv")
        if not os.path.exists(csv_path):
            pytest.skip("output/results.csv not found")

        df = ingest_reviews_csv(csv_path)
        assert df["id"].is_unique, "IDs should be unique after dedup"

    def test_ingest_handles_missing_file(self):
        """Test graceful handling of missing file."""
        with pytest.raises(Exception):
            ingest_reviews_csv("/nonexistent/path.csv")
