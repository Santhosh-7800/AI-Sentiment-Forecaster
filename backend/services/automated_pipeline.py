"""
Automated Pipeline Scheduler
Runs sentiment analysis and data updates automatically
Uses APScheduler for background tasks
"""
import logging
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from services.trending_fetcher import trending_fetcher
from services.quota_manager import quota_manager
from llm.sentiment_engine import get_sentiment
from database import db

logger = logging.getLogger(__name__)

class AutomatedPipeline:
    """Manages automated data collection and sentiment analysis"""

    def __init__(self):
        self.scheduler: Optional[BackgroundScheduler] = None
        self.is_running = False

    def start(self):
        """Start the automated pipeline scheduler"""
        if self.is_running:
            logger.warning("[WARN] Pipeline scheduler already running")
            return

        try:
            self.scheduler = BackgroundScheduler()

            # Run every 6 hours (respects free tier)
            self.scheduler.add_job(
                self.run_daily_update,
                CronTrigger(hour="*/6"),  # Every 6 hours
                id="daily_update",
                name="Daily product trend update",
                replace_existing=True
            )

            self.scheduler.start()
            self.is_running = True
            logger.info("[OK] Automated pipeline scheduler started")

        except Exception as e:
            logger.error(f"[FAIL] Failed to start pipeline scheduler: {e}")

    def stop(self):
        """Stop the scheduler"""
        if self.scheduler:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("[OK] Pipeline scheduler stopped")

<<<<<<< HEAD
    def run_daily_update(self, rotate_provider: bool = False):
=======
    def run_daily_update(self):
>>>>>>> 4463506 (Integrated TrendBot with Groq and polished UI styling)
        """
        Main task: Fetch trending data, analyze sentiment, store in MongoDB
        Runs silently if API quotas are exhausted
        """
        try:
            logger.info("[START] Running automated daily update pipeline...")

            # Step 1: Fetch trending products
            logger.info("Step 1: Fetching trending products...")
<<<<<<< HEAD
            trending_products = trending_fetcher.fetch_trending_products(rotate_provider=rotate_provider)
=======
            trending_products = trending_fetcher.fetch_trending_products()
>>>>>>> 4463506 (Integrated TrendBot with Groq and polished UI styling)

            if not trending_products:
                logger.info("[SKIP] No trending products fetched - quotas may be exhausted")
                return

            # Step 2: Fetch news for each product
            logger.info(f"Step 2: Fetching news for {len(trending_products)} products...")
<<<<<<< HEAD
            news_by_product = trending_fetcher.fetch_trending_news(trending_products, rotate_provider=rotate_provider)
=======
            news_by_product = trending_fetcher.fetch_trending_news(trending_products)
>>>>>>> 4463506 (Integrated TrendBot with Groq and polished UI styling)

            if not news_by_product:
                logger.info("[SKIP] No news articles fetched")
                return

            # Step 3: Analyze sentiment and store in MongoDB
            logger.info("Step 3: Analyzing sentiment and storing data...")
            self._store_analyzed_data(news_by_product)

            # Step 4: Log quota status
            quota_status = trending_fetcher.get_quota_status()
            logger.info(f"[OK] Pipeline complete. Quota status: {quota_status}")

        except Exception as e:
            logger.error(f"[FAIL] Pipeline error: {e}")

    def _store_analyzed_data(self, news_by_product: dict):
        """Analyze sentiment for each article and store in MongoDB"""
        collection = db["trending_products"]
        total_stored = 0

        for product, articles in news_by_product.items():
            try:
                analyzed_articles = []

                for article in articles:
                    try:
                        # Get sentiment
                        text = f"{article.get('title', '')} {article.get('description', '')}"
                        sentiment = get_sentiment(text)

                        analyzed_article = {
                            **article,
                            "product": product,
                            "sentiment_label": sentiment.get("label", "Neutral"),
                            "sentiment_score": sentiment.get("confidence_score", 0),
                            "analyzed_at": datetime.now().isoformat()
                        }
                        analyzed_articles.append(analyzed_article)

                    except Exception as e:
                        logger.warning(f"Failed to analyze sentiment for article: {e}")
                        continue

                # Store all articles for this product
                if analyzed_articles:
<<<<<<< HEAD
                    display_heading = analyzed_articles[0].get("display_heading", product)
                    context_type = analyzed_articles[0].get("context_type", "News")
                    context_category = analyzed_articles[0].get("context_category", "Tech Products")
                    context_region = analyzed_articles[0].get("context_region", "")
                    context_brand = analyzed_articles[0].get("context_brand", "")

=======
>>>>>>> 4463506 (Integrated TrendBot with Groq and polished UI styling)
                    update_result = collection.update_one(
                        {"product": product, "date": datetime.now().strftime("%Y-%m-%d")},
                        {
                            "$set": {
                                "product": product,
<<<<<<< HEAD
                                "keyword": display_heading,
                                "date": datetime.now().strftime("%Y-%m-%d"),
                                "articles": analyzed_articles,
                                "context_type": context_type,
                                "context_category": context_category,
                                "context_region": context_region,
                                "context_brand": context_brand,
                                "search_queries": sorted(
                                    list({a.get("search_query", product) for a in analyzed_articles if a.get("search_query")})
                                ),
=======
                                "date": datetime.now().strftime("%Y-%m-%d"),
                                "articles": analyzed_articles,
>>>>>>> 4463506 (Integrated TrendBot with Groq and polished UI styling)
                                "article_count": len(analyzed_articles),
                                "positive_count": sum(1 for a in analyzed_articles if a["sentiment_label"] == "Positive"),
                                "negative_count": sum(1 for a in analyzed_articles if a["sentiment_label"] == "Negative"),
                                "neutral_count": sum(1 for a in analyzed_articles if a["sentiment_label"] == "Neutral"),
                                "last_updated": datetime.now().isoformat()
                            }
                        },
                        upsert=True
                    )
                    total_stored += len(analyzed_articles)
                    logger.info(f"[OK] Stored {len(analyzed_articles)} articles for {product}")

            except Exception as e:
                logger.error(f"[FAIL] Error storing data for {product}: {e}")
                continue

        logger.info(f"[OK] Total articles stored: {total_stored}")

    def get_status(self) -> dict:
        """Get pipeline status"""
        return {
            "running": self.is_running,
            "scheduler_status": "active" if self.scheduler and self.scheduler.running else "inactive",
            "quota_status": trending_fetcher.get_quota_status(),
            "last_run": self._get_last_run_time()
        }

    def _get_last_run_time(self) -> Optional[str]:
        """Get timestamp of last successful pipeline run"""
        if not self.scheduler:
            return None

        job = self.scheduler.get_job("daily_update")
        if job and job.next_run_time:
            return job.next_run_time.isoformat()
        return None


# Global instance
pipeline = AutomatedPipeline()
