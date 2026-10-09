"""
Tests for Sentiment Model
==========================
Milestone 2: Unit tests for sentiment and topic models.

Run:
    pytest tests/test_models.py -v
"""
import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


class TestSentimentModel:
    """Tests for sentiment model."""

    @pytest.fixture(scope="class")
    def model(self):
        from models.sentiment_model import SentimentModel
        return SentimentModel()

    def test_positive_text(self, model):
        result = model.analyze("This product is amazing! Best purchase ever!")
        assert result["sentiment_label"] in ["positive", "very_positive"]
        assert result["sentiment_score"] > 0

    def test_negative_text(self, model):
        result = model.analyze("Terrible product. Total waste of money. Broke after one day.")
        assert result["sentiment_label"] in ["negative", "very_negative"]
        assert result["sentiment_score"] < 0

    def test_neutral_text(self, model):
        result = model.analyze("The product arrived on Tuesday.")
        assert result["sentiment_label"] == "neutral"
        assert -0.3 <= result["sentiment_score"] <= 0.3

    def test_empty_text(self, model):
        result = model.analyze("")
        assert result["sentiment_label"] == "neutral"
        assert result["sentiment_score"] == 0.0

    def test_batch_analysis(self, model):
        texts = ["Great product!", "Awful experience", "It works fine"]
        results = model.analyze_batch(texts, batch_size=2)
        assert len(results) == 3
        assert all("sentiment_label" in r for r in results)

    def test_score_range(self, model):
        result = model.analyze("Some text for testing score range")
        assert -1.0 <= result["sentiment_score"] <= 1.0

    def test_scores_dict_present(self, model):
        result = model.analyze("Test text")
        assert "scores" in result
        assert "negative" in result["scores"]
        assert "neutral" in result["scores"]
        assert "positive" in result["scores"]


class TestTopicModel:
    """Tests for topic model."""

    @pytest.fixture(scope="class")
    def model(self):
        from models.topic_model import TopicModel
        return TopicModel(method="keybert", num_topics=5)

    def test_extract_keywords(self, model):
        text = "The battery life on this smartphone is excellent and the camera quality is superb"
        keywords = model.extract_keywords(text)
        assert len(keywords) > 0
        assert isinstance(keywords[0], tuple)
        assert isinstance(keywords[0][0], str)  # keyword
        assert isinstance(keywords[0][1], float)  # score

    def test_empty_text_keywords(self, model):
        keywords = model.extract_keywords("")
        assert keywords == []

    def test_batch_topics(self, model):
        texts = [
            "The phone battery lasts all day which is great",
            "Camera quality is amazing for the price point",
            "Battery drains too fast need to charge every few hours",
            "The screen resolution is very clear and bright",
        ]
        result = model.extract_topics_batch(texts)
        assert "topics" in result
        assert "document_topics" in result
        assert len(result["document_topics"]) == 4
