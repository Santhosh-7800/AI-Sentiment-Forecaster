"""
Topic Model — Clean abstraction layer
======================================
Uses KeyBERT for keyword extraction and optionally BERTopic for full topic modeling.

Produces:
    - topic_id: int
    - topic_label: str
    - keywords: list of str
    - probabilities: list of float
"""
import logging
import re
import time
from collections import Counter
from typing import Dict, List, Any, Tuple

try:
    from keybert import KeyBERT
except ImportError:  # pragma: no cover - fallback for lightweight environments
    KeyBERT = None

logger = logging.getLogger(__name__)


class TopicModel:
    """
    Topic extraction using KeyBERT (fast) or BERTopic (richer).
    Default: KeyBERT for speed.
    """

    def __init__(self, method: str = "keybert", num_topics: int = 10, top_n: int = 5):
        """
        Args:
            method: 'keybert' or 'bertopic'
            num_topics: Target number of topics (BERTopic only)
            top_n: Number of keywords per topic/document
        """
        self.method = method
        self.num_topics = num_topics
        self.top_n = top_n
        self._keybert = None
        self._bertopic = None

    def _fallback_extract_keywords(self, text: str) -> List[Tuple[str, float]]:
        tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9']+", text.lower())
        stop_words = {
            "the", "and", "for", "with", "this", "that", "from", "into", "have",
            "has", "had", "were", "was", "is", "are", "on", "in", "of", "to",
            "a", "an", "it", "its", "as", "at", "be", "but", "not", "very", "more",
            "most", "than", "then", "there", "their", "they", "them", "you", "your",
            "our", "we", "he", "she", "his", "her", "who", "what", "when", "where"
        }
        filtered = [token for token in tokens if len(token) > 2 and token not in stop_words]
        counts = Counter(filtered)
        if not counts:
            return []
        top_items = counts.most_common(min(self.top_n, len(counts)))
        total = max(sum(count for _, count in top_items), 1)
        return [(word, round(count / total, 4)) for word, count in top_items]

    def _load_keybert(self):
        if self._keybert is None:
            if KeyBERT is None:
                logger.warning("KeyBERT is unavailable; using a lightweight heuristic keyword extractor.")
                self._keybert = False
            else:
                logger.info("Loading KeyBERT model...")
                self._keybert = KeyBERT("all-MiniLM-L6-v2")
                logger.info("KeyBERT model loaded.")

    def _load_bertopic(self):
        if self._bertopic is None:
            from bertopic import BERTopic
            logger.info("Loading BERTopic model...")
            self._bertopic = BERTopic(
                nr_topics=self.num_topics,
                verbose=False,
            )
            logger.info("BERTopic model loaded.")

    def extract_keywords(self, text: str) -> List[Tuple[str, float]]:
        """
        Extract keywords from a single document.

        Returns:
            List of (keyword, score) tuples
        """
        if not text or not text.strip():
            return []

        self._load_keybert()
        if self._keybert is False:
            return self._fallback_extract_keywords(text)

        try:
            keywords = self._keybert.extract_keywords(
                text,
                keyphrase_ngram_range=(1, 2),
                stop_words="english",
                top_n=self.top_n,
            )
            return keywords
        except Exception as e:
            logger.error(f"Keyword extraction error: {e}")
            return self._fallback_extract_keywords(text)

    def extract_topics_batch(self, texts: List[str]) -> Dict[str, Any]:
        """
        Extract topics from a batch of documents.

        For KeyBERT: extracts keywords per document and clusters them.
        For BERTopic: runs full topic modeling.

        Args:
            texts: List of cleaned text strings

        Returns:
            {
                "topics": [
                    {"topic_id": 0, "topic_label": "...", "keywords": [...], "count": N},
                    ...
                ],
                "document_topics": [
                    {"doc_index": i, "topic_id": int, "keywords": [...], "probabilities": [...]},
                    ...
                ]
            }
        """
        if not texts:
            return {"topics": [], "document_topics": []}

        start = time.time()

        if self.method == "bertopic" and len(texts) >= 10:
            return self._bertopic_extract(texts)
        else:
            return self._keybert_extract(texts)

    def _keybert_extract(self, texts: List[str]) -> Dict[str, Any]:
        """KeyBERT-based topic extraction."""
        self._load_keybert()
        start = time.time()

        document_topics = []
        all_keywords = {}

        for i, text in enumerate(texts):
            if not text.strip():
                document_topics.append({
                    "doc_index": i, "topic_id": -1,
                    "keywords": [], "probabilities": [],
                })
                continue

            kws = self.extract_keywords(text)
            keywords = [kw for kw, _ in kws]
            probs = [score for _, score in kws]

            # Simple topic assignment: hash top keyword to ID
            topic_key = keywords[0] if keywords else "unknown"
            if topic_key not in all_keywords:
                all_keywords[topic_key] = {
                    "topic_id": len(all_keywords),
                    "keywords": keywords,
                    "count": 0,
                }
            all_keywords[topic_key]["count"] += 1

            document_topics.append({
                "doc_index": i,
                "topic_id": all_keywords[topic_key]["topic_id"],
                "keywords": keywords,
                "probabilities": probs,
            })

        # Build topic summaries
        topics = []
        for key, info in all_keywords.items():
            topics.append({
                "topic_id": info["topic_id"],
                "topic_label": key,
                "keywords": info["keywords"],
                "count": info["count"],
            })

        topics.sort(key=lambda t: t["count"], reverse=True)

        latency = time.time() - start
        logger.info(f"KeyBERT extracted {len(topics)} topics from {len(texts)} docs in {latency:.2f}s")

        return {"topics": topics[:self.num_topics], "document_topics": document_topics}

    def _bertopic_extract(self, texts: List[str]) -> Dict[str, Any]:
        """BERTopic-based topic extraction."""
        self._load_bertopic()
        start = time.time()

        topics_ids, probs = self._bertopic.fit_transform(texts)
        topic_info = self._bertopic.get_topic_info()

        topics = []
        for _, row in topic_info.iterrows():
            tid = row["Topic"]
            if tid == -1:
                continue
            topic_words = self._bertopic.get_topic(tid)
            topics.append({
                "topic_id": tid,
                "topic_label": row.get("Name", f"Topic_{tid}"),
                "keywords": [w for w, _ in topic_words[:self.top_n]],
                "count": row.get("Count", 0),
            })

        document_topics = []
        for i, (tid, prob) in enumerate(zip(topics_ids, probs)):
            topic_words = self._bertopic.get_topic(tid) if tid != -1 else []
            document_topics.append({
                "doc_index": i,
                "topic_id": tid,
                "keywords": [w for w, _ in topic_words[:self.top_n]] if topic_words else [],
                "probabilities": prob.tolist() if hasattr(prob, "tolist") else [float(prob)],
            })

        latency = time.time() - start
        logger.info(f"BERTopic extracted {len(topics)} topics from {len(texts)} docs in {latency:.2f}s")

        return {"topics": topics, "document_topics": document_topics}


# Module-level singleton
_model = None


def get_topic_model(method: str = "keybert", num_topics: int = 10) -> TopicModel:
    """Get or create topic model singleton."""
    global _model
    if _model is None:
        _model = TopicModel(method=method, num_topics=num_topics)
    return _model
