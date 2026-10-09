"""
RAG Pipeline — Indexing enriched data into the vector store
============================================================
Loads enriched parquet data, chunks it, embeds it, and upserts into ChromaDB/Pinecone.

Usage:
    python -m pipelines.rag_index_pipeline
    python -m pipelines.rag_index_pipeline --input data/enriched/enriched_latest.parquet
"""
import os
import sys
import logging
import argparse
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("rag_index_pipeline")

ENRICHED_DIR = os.path.join(PROJECT_ROOT, "data", "enriched")


def index_enriched_data(input_path: str = None, batch_size: int = 50, max_retries: int = 3):
    """
    Index enriched data into the RAG vector store.

    Steps:
        1. Load enriched parquet
        2. Convert rows to LangChain Document objects with metadata
        3. Chunk using the existing DocumentProcessor
        4. Upsert into ChromaDB via VectorStoreManager

    Args:
        input_path: Path to enriched parquet. Defaults to enriched_latest.parquet
        batch_size: Number of documents to upsert per batch
        max_retries: Retry count for failed batches
    """
    import pandas as pd
    from langchain_core.documents import Document

    if input_path is None:
        input_path = os.path.join(ENRICHED_DIR, "enriched_latest.parquet")

    if not os.path.exists(input_path):
        logger.error(f"Enriched data not found: {input_path}")
        logger.info("Run pipelines first: python -m pipelines.sentiment_topic_pipeline")
        return

    logger.info(f"Loading enriched data from {input_path}")
    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} records")

    # Convert to LangChain documents
    documents = []
    for _, row in df.iterrows():
        text = str(row.get("clean_text", row.get("text", "")))
        if not text.strip():
            continue

        metadata = {
            "source": str(row.get("source", "")),
            "platform": str(row.get("platform", "")),
            "product_or_topic": str(row.get("product_or_topic", "")),
            "sentiment_label": str(row.get("sentiment_label", "")),
            "sentiment_score": float(row.get("sentiment_score", 0)),
            "topic_id": int(row.get("topic_id", -1)),
            "topic_label": str(row.get("topic_label", "")),
            "keywords": str(row.get("keywords", "")),
            "created_at": str(row.get("created_at", "")),
        }

        documents.append(Document(page_content=text, metadata=metadata))

    logger.info(f"Created {len(documents)} LangChain documents")

    if not documents:
        logger.warning("No documents to index.")
        return

    # Chunk documents using existing document processor
    try:
        from rag.document_processor import DocumentProcessor

        processor = DocumentProcessor()
        chunked_docs = processor.text_splitter.split_documents(documents)

        logger.info(f"Chunked into {len(chunked_docs)} chunks (from {len(documents)} docs)")
        documents = chunked_docs
    except ImportError:
        logger.warning("DocumentProcessor not available, indexing full documents (no chunking)")
    except Exception as e:
        logger.warning(f"Chunking failed ({e}), indexing full documents")

    # Upsert into vector store
    try:
        from rag.vector_store import VectorStoreManager
        from rag.rag_service import get_embedding_model

        embedding_model = get_embedding_model()
        vs = VectorStoreManager(embedding_model)

        total = len(documents)
        indexed = 0

        for i in range(0, total, batch_size):
            batch = documents[i : i + batch_size]
            retries = 0
            while retries < max_retries:
                try:
                    vs.add_documents(batch)
                    indexed += len(batch)
                    logger.info(f"Indexed batch {i//batch_size + 1}: {indexed}/{total}")
                    break
                except Exception as e:
                    retries += 1
                    logger.warning(f"Batch {i//batch_size + 1} failed (retry {retries}): {e}")
                    time.sleep(2 ** retries)
            else:
                logger.error(f"Batch {i//batch_size + 1} failed after {max_retries} retries, skipping")

        logger.info(f"RAG indexing complete. Indexed {indexed}/{total} documents.")

        stats = vs.get_stats()
        logger.info(f"Vector store stats: {stats}")

    except ImportError as e:
        logger.error(f"Vector store not available: {e}")
        logger.info("Install RAG deps: pip install -r backend/rag_requirements.txt")
    except Exception as e:
        logger.error(f"Indexing failed: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TrendAI RAG Index Pipeline")
    parser.add_argument("--input", type=str, default=None, help="Enriched parquet path")
    parser.add_argument("--batch-size", type=int, default=50)
    args = parser.parse_args()

    index_enriched_data(input_path=args.input, batch_size=args.batch_size)
