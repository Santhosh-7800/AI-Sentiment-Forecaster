"""
Realtime sentiment analysis service with cache + free-tier-aware source selection.
"""
from __future__ import annotations

import os
import re
import time
import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List

import requests
from requests import RequestException

from llm.sentiment_engine import get_sentiment
from scraper.news_scraper import scrape_news
from services.api_budget import ApiBudgetManager
from services.csv_fetcher import _fetch_local_csv_data

logger = logging.getLogger(__name__)

NEWS_API_URL = "https://newsapi.org/v2/everything"
PRICE_POSITIVE_TERMS = {"discount", "cheaper", "affordable", "deal", "sale", "price drop", "lower price"}
PRICE_NEGATIVE_TERMS = {"expensive", "overpriced", "price hike", "costly", "high price", "price increase"}


class RealtimeAnalyzer:
    def __init__(self) -> None:
        self.news_api_key = os.getenv("NEWS_API_KEY", "").strip()
        self.cache_ttl_seconds = int(os.getenv("REALTIME_CACHE_TTL_SECONDS", "300"))
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.budget = ApiBudgetManager()

    def _cache_key(self, product: str, max_articles: int) -> str:
        return f"{product.lower().strip()}::{max_articles}"

    def _read_cache(self, key: str) -> Dict[str, Any] | None:
        item = self._cache.get(key)
        if not item:
            return None
        if time.time() - item["ts"] > self.cache_ttl_seconds:
            return None
        return item["payload"]

    def _write_cache(self, key: str, payload: Dict[str, Any]) -> None:
        self._cache[key] = {"ts": time.time(), "payload": payload}

    def _fetch_newsapi(self, query: str, max_articles: int) -> List[Dict[str, Any]]:
        if not self.news_api_key:
            return []

        params = {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": min(max_articles, 100),
            "apiKey": self.news_api_key,
        }
        res = requests.get(NEWS_API_URL, params=params, timeout=20)
        res.raise_for_status()
        data = res.json()
        articles: List[Dict[str, Any]] = []
        for item in data.get("articles", []):
            articles.append(
                {
                    "platform": "newsapi",
                    "keyword": query,
                    "title": item.get("title") or "",
                    "description": item.get("description") or "",
                    "link": item.get("url") or "",
                    "published_date": item.get("publishedAt") or "",
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                }
            )
        return articles

    def _fetch_with_budget_control(self, query: str, max_articles: int) -> tuple[List[Dict[str, Any]], str, Dict[str, Any]]:
        budget_status = self.budget.status()
        
        # 1. Fetch from local output CSVs (the "real offline data")
        csv_articles = _fetch_local_csv_data(query)

        # 2. Fetch from APIs
        api_articles = []
        if self.news_api_key and self.budget.can_consume(1):
            try:
                api_articles = self._fetch_newsapi(query, max_articles)
                budget_status = self.budget.consume(1)
            except Exception:
                pass

        if not api_articles:
            try:
                api_articles = scrape_news(keywords=[query], max_articles=max_articles)
            except Exception:
                pass

        combined = csv_articles + api_articles
        # Slice back to reasonable limits to avoid overloading the LLM sentiment parsing
        combined = combined[:max_articles * 2] 
        source = "local_csv_and_api" if csv_articles and api_articles else ("local_csv" if csv_articles else "api")
        return combined, source, budget_status

    def _bucket_day(self, published_date: str) -> str:
        if not published_date:
            return datetime.now(timezone.utc).strftime("%Y-%m-%d")
        try:
            normalized = published_date.replace("Z", "+00:00")
            dt = datetime.fromisoformat(normalized)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            # Handles rss dates like: Mon, 10 Feb 2026 07:20:00 GMT
            try:
                dt = datetime.strptime(published_date, "%a, %d %b %Y %H:%M:%S %Z")
                return dt.strftime("%Y-%m-%d")
            except Exception:
                return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def _bucket_year(self, published_date: str) -> int:
        if not published_date:
            return datetime.now(timezone.utc).year
        try:
            normalized = published_date.replace("Z", "+00:00")
            dt = datetime.fromisoformat(normalized)
            return dt.year
        except Exception:
            try:
                dt = datetime.strptime(published_date, "%a, %d %b %Y %H:%M:%S %Z")
                return dt.year
            except Exception:
                try:
                    # Attempt parsing standard 06-02-2026 simple dates
                    dt = datetime.strptime(published_date[:10], "%d-%m-%Y")
                    return dt.year
                except Exception:
                    return datetime.now(timezone.utc).year

    def _bucket_month(self, published_date: str) -> int:
        if not published_date:
            return datetime.now(timezone.utc).month
        try:
            normalized = published_date.replace("Z", "+00:00")
            dt = datetime.fromisoformat(normalized)
            return dt.month
        except Exception:
            try:
                dt = datetime.strptime(published_date, "%a, %d %b %Y %H:%M:%S %Z")
                return dt.month
            except Exception:
                try:
                    dt = datetime.strptime(published_date[:10], "%d-%m-%Y")
                    return dt.month
                except Exception:
                    return datetime.now(timezone.utc).month

    def _extract_prices(self, text: str) -> List[float]:
        """Extract likely INR-like prices from article text.

        DISABLED: Price extraction from review text was unreliable and pulled random
        numbers (e.g., "238 reviews", "768 ratings") instead of actual product prices.
        Returns empty list to disable price data extraction.
        TODO: Implement proper price tracking via dedicated price column in CSVs or
        external product database API.
        """
        return []

    def _infer_start_year(self, product: str) -> int:
        current_year = datetime.now(timezone.utc).year
        year_match = re.search(r"\b(19\d{2}|20\d{2})\b", product)
        if year_match:
            return int(year_match.group(1))
        return current_year - 6

    def _price_signal(self, text: str) -> str:
        t = text.lower()
        if any(term in t for term in PRICE_NEGATIVE_TERMS):
            return "price_negative"
        if any(term in t for term in PRICE_POSITIVE_TERMS):
            return "price_positive"
        return "neutral"

    def _normalize_sentiment(self, label: str) -> str:
        """Normalize sentiment labels from various sources to standard format."""
        label = str(label).lower().strip()
        if any(x in label for x in ['pos', 'positive', '+1', 'good']):
            return "Positive"
        elif any(x in label for x in ['neg', 'negative', '-1', 'bad']):
            return "Negative"
        else:
            return "Neutral"

    def analyze_product(self, product: str, max_articles: int = 25, force_refresh: bool = False) -> Dict[str, Any]:
        product = (product or "").strip()
        if not product:
            raise ValueError("product is required")

        logger.info(f"[TARGET] Starting analysis for: '{product}' (force_refresh={force_refresh})")
        
        cache_key = self._cache_key(product, max_articles)
        if not force_refresh:
            cached = self._read_cache(cache_key)
            if cached:
                logger.info(f"[OK] Cache hit for '{product}'")
                return {**cached, "cached": True}

        logger.info(f" Fetching articles for '{product}'...")
        articles, source, budget = self._fetch_with_budget_control(product, max_articles)
        logger.info(f"[OK] Fetched {len(articles)} articles from {source}")

        if not articles:
            logger.warning(f"[WARN]  No articles found for '{product}'")
            payload = {
                "product": product,
                "source": source,
                "budget": budget,
                "cached": False,
                "article_count": 0,
                "sentiment_breakdown": {"positive": 0, "neutral": 0, "negative": 0},
                "sentiment_score": 0,
                "daily_trend": [],
                "price_sensitivity": {
                    "price_positive_mentions": 0,
                    "price_negative_mentions": 0,
                    "price_sensitivity_index": 0,
                },
                "summary": "No recent public articles found for this product.",
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
            self._write_cache(cache_key, payload)
            return payload

        sentiment_counter = {"Positive": 0, "Neutral": 0, "Negative": 0}
        daily_scores: Dict[str, List[int]] = defaultdict(list)
        yearly_scores: Dict[int, List[int]] = defaultdict(list)
        yearly_prices: Dict[int, List[float]] = defaultdict(list)
        current_year_monthly_prices: Dict[int, List[float]] = defaultdict(list)
        price_positive_mentions = 0
        price_negative_mentions = 0

        enriched_articles: List[Dict[str, Any]] = []

        current_year = datetime.now(timezone.utc).year

        logger.info(f"[SYNC] Processing {len(articles)} articles for sentiment analysis...")
        processed_count = 0
        
        for article in articles:
            text = f"{article.get('title', '')} {article.get('description', '')}".strip()
            if not text or len(text) < 10:
                continue
            
            processed_count += 1
            if processed_count % 10 == 0:
                logger.info(f"    Processed {processed_count}/{len(articles)} articles...")

            # Try using pre-labeled sentiment from CSV first (faster & more reliable)
            if 'csv_sentiment' in article:
                label = self._normalize_sentiment(article['csv_sentiment'])
                confidence = 0.85  # CSV labels are reliable
            else:
                # Fall back to LLM sentiment for API articles
                try:
                    sentiment = get_sentiment(text)
                    label = sentiment.get("label", "Neutral")
                    confidence = sentiment.get("confidence_score", 0)
                except Exception as e:
                    logger.warning(f"   [WARN]  Sentiment analysis failed: {str(e)}")
                    label = "Neutral"
                    confidence = 0

            sentiment_counter[label] = sentiment_counter.get(label, 0) + 1

            score_map = {"Positive": 1, "Neutral": 0, "Negative": -1}
            day = self._bucket_day(article.get("published_date", ""))
            year = self._bucket_year(article.get("published_date", ""))
            month = self._bucket_month(article.get("published_date", ""))
            
            daily_scores[day].append(score_map.get(label, 0))
            yearly_scores[year].append(score_map.get(label, 0))

            prices = self._extract_prices(text)
            if prices:
                yearly_prices[year].extend(prices)
                if year == current_year:
                    current_year_monthly_prices[month].extend(prices)

            price_signal = self._price_signal(text)
            if price_signal == "price_positive":
                price_positive_mentions += 1
            elif price_signal == "price_negative":
                price_negative_mentions += 1

            enriched_articles.append(
                {
                    **article,
                    "sentiment_label": label,
                    "confidence_score": confidence,
                    "price_signal": price_signal,
                }
            )

        total = max(sum(sentiment_counter.values()), 1)
        sentiment_score = round(
            ((sentiment_counter["Positive"] - sentiment_counter["Negative"]) / total) * 100,
            2,
        )

        trend = []
        for day in sorted(daily_scores.keys()):
            values = daily_scores[day]
            if not values:
                continue
            avg = sum(values) / len(values)
            trend.append({"date": day, "score": round(avg, 3), "samples": len(values)})

        start_year = self._infer_start_year(product)
        current_year = datetime.now(timezone.utc).year
        if yearly_scores:
            start_year = min(start_year, min(yearly_scores.keys()))

        yearly_sentiment_trend = []
        yearly_price_trend = []
        for year in range(start_year, current_year + 1):
            y_scores = yearly_scores.get(year, [])
            y_prices = yearly_prices.get(year, [])

            year_score = round(sum(y_scores) / len(y_scores), 3) if y_scores else 0.0
            avg_price = round(sum(y_prices) / len(y_prices), 2) if y_prices else None

            yearly_sentiment_trend.append({
                "year": year,
                "score": year_score,
                "samples": len(y_scores),
            })
            yearly_price_trend.append({
                "year": year,
                "avg_price": avg_price,
                "samples": len(y_prices),
            })
            
        current_year_monthly_trend = []
        for m in range(1, 13):
            m_prices = current_year_monthly_prices.get(m, [])
            avg_price = round(sum(m_prices) / len(m_prices), 2) if m_prices else None
            current_year_monthly_trend.append({
                "month": m,
                "avg_price": avg_price,
                "samples": len(m_prices)
            })
            
        psi_denominator = max(price_positive_mentions + price_negative_mentions, 1)
        price_sensitivity_index = round(
            ((price_negative_mentions - price_positive_mentions) / psi_denominator) * 100,
            2,
        )

        summary = (
            f"{product}: {sentiment_counter['Positive']} positive, "
            f"{sentiment_counter['Neutral']} neutral, {sentiment_counter['Negative']} negative mentions. "
            f"Price sensitivity index is {price_sensitivity_index} (higher means more negative reaction to price changes)."
        )

        dominant_label = "Neutral"
        if sentiment_counter["Positive"] >= sentiment_counter["Negative"] and sentiment_counter["Positive"] >= sentiment_counter["Neutral"]:
            dominant_label = "Positive"
        elif sentiment_counter["Negative"] >= sentiment_counter["Positive"] and sentiment_counter["Negative"] >= sentiment_counter["Neutral"]:
            dominant_label = "Negative"

        insights = [
            f"Dominant sentiment for {product} is {dominant_label}.",
            f"Sentiment score is {sentiment_score}, where positive means better customer outlook.",
            f"Price sensitivity index is {price_sensitivity_index}; higher values indicate stronger negative response to price increases.",
            f"Analyzed {len(enriched_articles)} recent mentions from {source}.",
        ]

        payload = {
            "product": product,
            "source": source,
            "budget": budget,
            "cached": False,
            "article_count": len(enriched_articles),
            "sentiment_breakdown": {
                "positive": sentiment_counter["Positive"],
                "neutral": sentiment_counter["Neutral"],
                "negative": sentiment_counter["Negative"],
            },
            "sentiment_score": sentiment_score,
            "daily_trend": trend,
            "yearly_sentiment_trend": yearly_sentiment_trend,
            "yearly_price_trend": yearly_price_trend,
            "current_year_monthly_trend": current_year_monthly_trend,
            "price_sensitivity": {
                "price_positive_mentions": price_positive_mentions,
                "price_negative_mentions": price_negative_mentions,
                "price_sensitivity_index": price_sensitivity_index,
            },
            "analysis_window": {
                "start_year": start_year,
                "end_year": current_year,
            },
            "insights": insights,
            "top_articles": enriched_articles[: min(len(enriched_articles), 8)],
            "summary": summary,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(f"[OK] Analysis complete for '{product}': {sentiment_counter['Positive']} positive, {sentiment_counter['Neutral']} neutral, {sentiment_counter['Negative']} negative")
        
        self._write_cache(cache_key, payload)
        return payload
