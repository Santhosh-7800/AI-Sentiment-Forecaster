"""
Trending Data Fetcher
Fetches trending daily products and news respecting quotas
"""
import os
import logging
import requests
import re
from typing import List, Dict, Any
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from services.quota_manager import quota_manager

logger = logging.getLogger(__name__)


def _load_env_once() -> None:
    """Load .env from backend/ or project root so service works in any entrypoint."""
    backend_root = Path(__file__).resolve().parents[1]
    project_root = backend_root.parent

    load_dotenv(backend_root / ".env", override=False)
    load_dotenv(project_root / ".env", override=False)


_load_env_once()

class TrendingDataFetcher:
    """Fetches trending products and news while respecting free tier quotas"""

    _STOPWORDS = {
        "the", "a", "an", "and", "or", "for", "to", "of", "in", "on", "with", "from", "by", "at",
        "is", "are", "was", "were", "be", "been", "being", "it", "its", "this", "that", "these", "those",
        "new", "latest", "best", "top", "trending", "popular", "today", "daily", "global", "market",
        "product", "products", "launch", "launches", "review", "reviews", "news", "update", "updates",
        "shows", "report", "reports", "guide", "vs", "how", "what", "why", "you", "your", "our"
    }

    _WEAK_TERMS = {
        "women", "men", "people", "consumer", "consumers", "brand", "brands", "company", "companies"
    }

    _GENERIC_BRAND_TOKENS = {"The", "This", "That", "These", "Those", "How", "Why", "What", "Top", "Best"}

    _KNOWN_BRANDS = [
        "Apple", "Samsung", "Google", "Xiaomi", "OnePlus", "Vivo", "Oppo", "Realme", "Huawei",
        "Sony", "LG", "Lenovo", "Asus", "Acer", "HP", "Dell", "Microsoft", "Nokia", "Nothing",
        "Motorola", "Honor", "Tesla", "BYD", "Toyota", "Hyundai", "Bose", "JBL", "Boat", "Garmin"
    ]

    _CATEGORY_RULES = [
        ("foldable smartphone", "Foldable Smartphones"),
        ("foldable phone", "Foldable Smartphones"),
        ("smartphone", "Smartphones"),
        ("phone", "Smartphones"),
        ("iphone", "Smartphones"),
        ("android", "Smartphones"),
        ("laptop", "Laptops"),
        ("notebook", "Laptops"),
        ("tablet", "Tablets"),
        ("smartwatch", "Smartwatches"),
        ("watch", "Smartwatches"),
        ("earbuds", "Earbuds"),
        ("earbud", "Earbuds"),
        ("headphones", "Headphones"),
        ("headphone", "Headphones"),
        ("car", "Cars"),
        ("ev", "Electric Vehicles"),
        ("electric vehicle", "Electric Vehicles"),
        ("gaming", "Gaming Devices"),
        ("console", "Gaming Devices"),
        ("appliance", "Home Appliances"),
        ("tv", "Smart TVs"),
    ]

    _REGION_RULES = [
        ("chinese", "China"),
        ("china", "China"),
        ("india", "India"),
        ("indian", "India"),
        ("europe", "Europe"),
        ("uk", "UK"),
        ("britain", "UK"),
        ("united states", "US"),
        ("us", "US"),
        ("america", "US"),
        ("japan", "Japan"),
        ("korea", "Korea"),
    ]

    _INTENT_RULES = [
        (["review", "hands-on", "test", "rating", "verdict"], "Reviews"),
        (["launch", "launched", "release", "released", "unveil", "debut"], "Launch"),
        (["leak", "rumor", "rumoured", "teaser"], "Leaks"),
        (["price", "pricing", "cost", "discount", "deal"], "Pricing"),
        (["vs", "compare", "comparison"], "Comparisons"),
    ]

    _SEED_KEYWORDS = [
        "consumer electronics trends",
        "smartphone launch",
        "laptop review",
        "wearable technology",
        "headphones and earbuds",
        "home appliances innovation",
        "gaming gadgets",
    ]

    def __init__(self):
        # Don't load API keys in __init__ - they may not be loaded yet
        # Load them lazily when needed
        self._provider_cursor = 0

    def _get_api_keys(self):
        """Get API keys lazily to ensure .env is loaded"""
        # Support both NEWS_API_KEY and NEWSAPI_KEY naming conventions.
        news_api_key = os.getenv("NEWS_API_KEY", "").strip() or os.getenv("NEWSAPI_KEY", "").strip()
        gnews_api_key = os.getenv("GNEWS_API_KEY", "").strip()
        return {
            "news_api_key": news_api_key,
            "gnews_api_key": gnews_api_key,
            "gemini_api_key": os.getenv("GOOGLE_API_KEY", "").strip()
        }

    def _available_news_providers(self, rotate: bool = False) -> List[str]:
        keys = self._get_api_keys()
        providers = []
        if keys.get("news_api_key"):
            providers.append("newsapi")
        if keys.get("gnews_api_key"):
            providers.append("gnews")
        if rotate and len(providers) > 1:
            offset = self._provider_cursor % len(providers)
            providers = providers[offset:] + providers[:offset]
            self._provider_cursor = (self._provider_cursor + 1) % len(providers)
        return providers

    def _fetch_articles_from_provider(self, provider: str, query: str, page_size: int) -> List[Dict[str, Any]]:
        keys = self._get_api_keys()

        if provider == "newsapi":
            api_key = keys.get("news_api_key", "")
            if not api_key:
                return []
            params = {
                "q": query,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": page_size,
                "apiKey": api_key,
            }
            response = requests.get("https://newsapi.org/v2/everything", params=params, timeout=10)
            if response.status_code == 200 and quota_manager.consume("newsapi"):
                return response.json().get("articles", [])
            return []

        if provider == "gnews":
            api_key = keys.get("gnews_api_key", "")
            if not api_key:
                return []
            params = {
                "q": query,
                "lang": "en",
                "max": page_size,
                "sortby": "publishedAt",
                "token": api_key,
            }
            response = requests.get("https://gnews.io/api/v4/search", params=params, timeout=10)
            if response.status_code == 200 and quota_manager.consume("gnews"):
                return response.json().get("articles", [])
            return []

        return []

    def _normalize_article(self, provider: str, article: Dict[str, Any]) -> Dict[str, Any]:
        source = article.get("source") or {}
        if isinstance(source, str):
            source_name = source
        else:
            source_name = source.get("name", "")

        return {
            "title": article.get("title", ""),
            "description": article.get("description", ""),
            "url": article.get("url", ""),
            "source": source_name,
            "published_at": article.get("publishedAt", ""),
            "content": article.get("content", ""),
            "provider": provider,
        }

    def _tokenize(self, text: str) -> List[str]:
        cleaned = re.sub(r"[^A-Za-z0-9\s\-]", " ", (text or "").lower())
        parts = re.split(r"[\s\-]+", cleaned)
        return [p for p in parts if p]

    def _extract_brand(self, title: str, text: str) -> str:
        lower_text = (text or "").lower()
        lower_title = (title or "").lower()

        for brand in self._KNOWN_BRANDS:
            if re.search(rf"\b{re.escape(brand.lower())}\b", lower_title):
                return brand
        for brand in self._KNOWN_BRANDS:
            if re.search(rf"\b{re.escape(brand.lower())}\b", lower_text):
                return brand

        possessive = re.search(r"\b([A-Z][a-zA-Z0-9]+)'s\b", title or "")
        if possessive:
            candidate = possessive.group(1)
            if candidate not in self._GENERIC_BRAND_TOKENS:
                return candidate

        leading = re.search(r"\b([A-Z][a-zA-Z0-9]+)\b", title or "")
        if leading:
            candidate = leading.group(1)
            if candidate not in self._GENERIC_BRAND_TOKENS:
                return candidate

        return ""

    def _extract_category(self, text: str) -> str:
        lower = (text or "").lower()
        for token, label in self._CATEGORY_RULES:
            if re.search(rf"\b{re.escape(token)}\b", lower):
                return label
        return "Tech Products"

    def _extract_region(self, text: str) -> str:
        lower = (text or "").lower()
        for token, label in self._REGION_RULES:
            if re.search(rf"\b{re.escape(token)}\b", lower):
                return label
        return ""

    def _extract_intent(self, text: str) -> str:
        lower = (text or "").lower()
        for terms, label in self._INTENT_RULES:
            if any(term in lower for term in terms):
                return label
        return "News"

    def _compose_search_keyword(self, brand: str, region: str, category: str) -> str:
        parts = [p for p in [brand, region, category] if p]
        return " ".join(parts).strip()

    def _compose_display_heading(self, search_keyword: str, intent: str) -> str:
        base = (search_keyword or "Tech Products").strip()
        if intent and intent != "News":
            return f"{base} - {intent}"
        return base

    def _extract_context(self, title: str, description: str) -> Dict[str, str]:
        text = f"{title or ''} {description or ''}".strip()
        brand = self._extract_brand(title or "", text)
        category = self._extract_category(text)
        region = self._extract_region(text)
        intent = self._extract_intent(text)

        search_keyword = self._compose_search_keyword(brand, region, category)
        if not search_keyword:
            search_keyword = category or "Tech Products"

        heading = self._compose_display_heading(search_keyword, intent)
        return {
            "brand": brand,
            "region": region,
            "category": category,
            "intent": intent,
            "search_keyword": search_keyword,
            "heading": heading,
        }

    def _infer_heading_from_articles(self, fallback_keyword: str, articles: List[Dict[str, Any]]) -> Dict[str, str]:
        if not articles:
            return {
                "search_keyword": fallback_keyword,
                "heading": fallback_keyword,
                "intent": "News",
                "category": "Tech Products",
                "region": "",
                "brand": "",
            }

        intent_scores: Dict[str, int] = defaultdict(int)
        category_scores: Dict[str, int] = defaultdict(int)
        region_scores: Dict[str, int] = defaultdict(int)
        brand_scores: Dict[str, int] = defaultdict(int)

        for article in articles:
            context = self._extract_context(article.get("title", ""), article.get("description", ""))
            intent_scores[context["intent"]] += 1
            category_scores[context["category"]] += 1
            if context["region"]:
                region_scores[context["region"]] += 1
            if context["brand"]:
                brand_scores[context["brand"]] += 1

        intent = max(intent_scores, key=intent_scores.get) if intent_scores else "News"
        category = max(category_scores, key=category_scores.get) if category_scores else "Tech Products"
        region = max(region_scores, key=region_scores.get) if region_scores else ""
        brand = max(brand_scores, key=brand_scores.get) if brand_scores else ""

        search_keyword = self._compose_search_keyword(brand, region, category) or fallback_keyword
        heading = self._compose_display_heading(search_keyword, intent)

        return {
            "search_keyword": search_keyword,
            "heading": heading,
            "intent": intent,
            "category": category,
            "region": region,
            "brand": brand,
        }

    def _build_keyword_scores(self, title: str, description: str) -> Dict[str, int]:
        """Score unigrams/bigrams so headings are concise, searchable product keywords."""
        title_tokens = self._tokenize(title)
        desc_tokens = self._tokenize(description)
        all_tokens = title_tokens + desc_tokens
        scores: Dict[str, int] = {}

        filtered_tokens = [
            t for t in all_tokens
            if len(t) >= 3 and t not in self._STOPWORDS and not t.isdigit()
        ]

        for token in filtered_tokens:
            if token in self._WEAK_TERMS:
                continue
            scores[token] = scores.get(token, 0) + 1
            if token in title_tokens:
                scores[token] += 2

        for i in range(len(filtered_tokens) - 1):
            a, b = filtered_tokens[i], filtered_tokens[i + 1]
            if a == b:
                continue
            phrase = f"{a} {b}"
            scores[phrase] = scores.get(phrase, 0) + 3
            if phrase in " ".join(title_tokens):
                scores[phrase] += 2

        return scores

    def _normalize_keyword(self, keyword: str) -> str:
        cleaned = re.sub(r"\s+", " ", re.sub(r"[^A-Za-z0-9\s]", " ", keyword or "")).strip()
        if not cleaned:
            return ""
        words = cleaned.split()
        if len(words) > 3:
            words = words[:3]
        return " ".join(words).title()

    def _build_search_query(self, keyword: str) -> str:
        """Use focused query terms to improve relevancy and reduce noisy article matches."""
        k = (keyword or "").strip()
        if not k:
            return ""
        return f'"{k}" AND (review OR launch OR features OR price OR specs OR comparison)'

    def fetch_trending_products(self, rotate_provider: bool = False) -> List[str]:
        """
        Fetch trending daily products from NewsAPI
        Returns: List of product names in trend
        """
        keys = self._get_api_keys()
        providers = self._available_news_providers(rotate=rotate_provider)
        if not providers:
            logger.error("[FAIL] No news provider key configured. Add NEWS_API_KEY and/or GNEWS_API_KEY.")
            return []

        try:
            keyword_scores: Dict[str, int] = defaultdict(int)
            keyword_meta: Dict[str, Dict[str, str]] = {}

            for seed in self._SEED_KEYWORDS:
                articles: List[Dict[str, Any]] = []
                for provider in providers:
                    if not quota_manager.can_use(provider):
                        continue
                    articles = self._fetch_articles_from_provider(provider, seed, 10)
                    if articles:
                        logger.info(f"[OK] Seed '{seed}' fetched via {provider.upper()}")
                        break
                if not articles:
                    continue

                for article in articles:
                    title = article.get("title", "")
                    description = article.get("description", "")
                    context = self._extract_context(title, description)
                    search_keyword = context["search_keyword"]

                    if not search_keyword:
                        continue

                    score = 1
                    if context["brand"]:
                        score += 2
                    if context["category"] and context["category"] != "Tech Products":
                        score += 2
                    if context["region"]:
                        score += 1
                    if context["intent"] in {"Reviews", "Launch", "Pricing", "Comparisons"}:
                        score += 1

                    keyword_scores[search_keyword] += score
                    keyword_meta[search_keyword] = context

            ranked_keywords = sorted(keyword_scores.items(), key=lambda x: x[1], reverse=True)
            selected: List[str] = []
            selected_token_sets = []

            for raw_keyword, _ in ranked_keywords:
                normalized = self._normalize_keyword(raw_keyword)
                if not normalized or len(normalized) < 3:
                    continue

                tokens = set(self._tokenize(normalized))
                if not tokens:
                    continue

                # De-duplicate near-identical keywords to improve search quality.
                too_similar = False
                for existing_tokens in selected_token_sets:
                    overlap = len(tokens & existing_tokens)
                    min_size = max(1, min(len(tokens), len(existing_tokens)))
                    if overlap / min_size >= 0.8:
                        too_similar = True
                        break

                if too_similar:
                    continue

                selected.append(normalized)
                selected_token_sets.append(tokens)
                if len(selected) >= 10:
                    break

            logger.info(f"[OK] Extracted {len(selected)} optimized trending keywords")
            return selected

        except Exception as e:
            logger.error(f"[FAIL] Error fetching trending products: {e}")
            return []

    def fetch_trending_news(self, products: List[str], rotate_provider: bool = False) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch trending news for each product
        Returns: {product: [articles]}
        """
        keys = self._get_api_keys()
        providers = self._available_news_providers(rotate=rotate_provider)
        if not providers:
            logger.error("[FAIL] No news provider key configured. Add NEWS_API_KEY and/or GNEWS_API_KEY.")
            return {}

        news_by_product = {}

        for product in products:
            if not any(quota_manager.can_use(provider) for provider in providers):
                logger.warning("[WARN] All news provider quotas exhausted - stopping news fetch")
                break

            try:
                query = self._build_search_query(product)
                articles: List[Dict[str, Any]] = []
                active_provider = ""

                for provider in providers:
                    if not quota_manager.can_use(provider):
                        continue
                    raw_articles = self._fetch_articles_from_provider(provider, query or product, 15)
                    if raw_articles:
                        articles = [self._normalize_article(provider, a) for a in raw_articles]
                        active_provider = provider
                        break

                # Fallback to simple keyword query if strict query produced no results.
                if not articles:
                    for provider in providers:
                        if not quota_manager.can_use(provider):
                            continue
                        raw_articles = self._fetch_articles_from_provider(provider, product, 10)
                        if raw_articles:
                            articles = [self._normalize_article(provider, a) for a in raw_articles]
                            active_provider = provider
                            break

                if articles:

                    heading_context = self._infer_heading_from_articles(product, articles)

                    news_by_product[product] = [
                        {
                            "title": article.get("title", ""),
                            "description": article.get("description", ""),
                            "url": article.get("url", ""),
                            "source": article.get("source", ""),
                            "published_at": article.get("published_at", ""),
                            "content": article.get("content", ""),
                            "provider": article.get("provider", active_provider),
                            "search_keyword": heading_context["search_keyword"],
                            "search_query": query or product,
                            "display_heading": heading_context["heading"],
                            "context_type": heading_context["intent"],
                            "context_category": heading_context["category"],
                            "context_region": heading_context["region"],
                            "context_brand": heading_context["brand"],
                        }
                        for article in articles[:5]  # Top 5 per product
                    ]

                    logger.info(
                        f"[OK] Fetched {len(news_by_product[product])} articles for {product} via {active_provider.upper() if active_provider else 'UNKNOWN'}"
                    )

            except Exception as e:
                logger.error(f"[FAIL] Error fetching news for {product}: {e}")
                continue

        return news_by_product

    def get_quota_status(self) -> Dict[str, Any]:
        """Get current quota status"""
        return {
            "newsapi": quota_manager.get_status("newsapi"),
            "gnews": quota_manager.get_status("gnews"),
            "gemini": quota_manager.get_status("gemini"),
            "timestamp": datetime.now().isoformat()
        }


# Global instance
trending_fetcher = TrendingDataFetcher()
