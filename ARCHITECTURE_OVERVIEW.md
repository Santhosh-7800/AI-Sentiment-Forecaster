# Architecture Overview — AI-Powered Market Trend & Consumer Sentiment Forecaster

## High-Level System Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        DATA COLLECTION LAYER                            │
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │ Amazon Review │  │ Google News  │  │ Social Media │                  │
│  │   Scraper     │  │   Scraper    │  │   (future)   │                  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                  │
│         └─────────────────┼─────────────────┘                          │
│                           ▼                                             │
│              ┌────────────────────────┐                                 │
│              │  Data Cleaning &       │                                 │
│              │  Normalization Pipeline │                                │
│              └────────────┬───────────┘                                 │
│                           ▼                                             │
│              ┌────────────────────────┐                                 │
│              │  data/processed/       │  (Parquet/JSONL, common schema) │
│              └────────────────────────┘                                 │
└─────────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   LLM SENTIMENT & TOPIC ENGINE                          │
│                                                                         │
│  ┌──────────────────────┐    ┌──────────────────────┐                  │
│  │  Sentiment Model      │    │  Topic Model          │                  │
│  │  (RoBERTa + Groq LLM)│    │  (BERTopic + KeyBERT) │                  │
│  │  → label + score      │    │  → topic_id, keywords  │                  │
│  └──────────┬───────────┘    └──────────┬───────────┘                  │
│             └───────────────────────────┘                               │
│                           ▼                                             │
│              ┌────────────────────────┐                                 │
│              │  data/enriched/        │  (+ sentiment, topics, scores)  │
│              └────────────────────────┘                                 │
└─────────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   RAG PIPELINE (LangChain + ChromaDB/Pinecone)          │
│                                                                         │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐            │
│  │ Document       │  │ Embeddings     │  │ Vector Store   │            │
│  │ Chunker        │→ │ (MiniLM-L6)   │→ │ (ChromaDB)     │            │
│  └────────────────┘  └────────────────┘  └────────┬───────┘            │
│                                                    │                    │
│  ┌────────────────┐  ┌────────────────┐           │                    │
│  │ Query Engine   │← │ LLM (Groq      │←──────────┘                    │
│  │ (retriever +   │  │  Llama 3.3)    │  top-k retrieval               │
│  │  QA chain)     │  └────────────────┘                                │
│  └────────────────┘                                                     │
│         ▼                                                               │
│  POST /api/rag/query → grounded natural language answers + references   │
└─────────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   ANALYTICS & TREND ENGINE                              │
│                                                                         │
│  ┌────────────────────────┐  ┌────────────────────────┐                │
│  │ Trend Analytics        │  │ Aggregation Layer       │                │
│  │ (regression, spikes,   │  │ (group by date/product/ │                │
│  │  forecasting)          │  │  topic → mean, counts)  │                │
│  └────────────┬───────────┘  └────────────┬───────────┘                │
│               └───────────────────────────┘                             │
│                           ▼                                             │
│              ┌────────────────────────┐                                 │
│              │  data/analytics/       │  (aggregated parquets)          │
│              └────────────────────────┘                                 │
└─────────────────────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┼──────────────┐
              ▼             ▼              ▼
┌──────────────────┐ ┌────────────┐ ┌────────────────┐
│  DASHBOARDS      │ │  ALERTS    │ │  REPORTS       │
│  (React + Vite)  │ │  ENGINE    │ │  GENERATOR     │
│                  │ │            │ │                │
│  /dashboard      │ │ Sentiment  │ │ PDF (ReportLab)│
│  /sentiment      │ │ spike      │ │ Excel (openpyxl│
│  /market-trends  │ │ detection, │ │                │
│  /analytics      │ │ volume     │ │ Weekly/monthly │
│  /reports        │ │ alerts,    │ │ summaries with │
│                  │ │ rule-based │ │ trends, RAG    │
│  FastAPI backend │ │ thresholds │ │ insights       │
│  ← API calls →   │ │ → log +   │ │                │
└──────────────────┘ │   notify  │ └────────────────┘
                     └────────────┘

```

## Data Flow

```
Raw Input (CSV/scrape)
  → data_collection/ scrapers fetch from Amazon, Google News, social APIs
  → utils/cleaner.py normalizes text (lowercase, URL removal, dedup)
  → data/processed/*.parquet (common schema: id, source, platform, text, created_at, ...)
  → models/sentiment_model.py scores each record (label + score -1.0 to 1.0)
  → models/topic_model.py assigns topic_id, topic_label, keywords
  → data/enriched/*.parquet (original + sentiment + topics)
  → rag/document_chunking.py chunks enriched docs
  → rag/vector_store.py upserts embeddings into ChromaDB/Pinecone
  → rag/query_engine.py answers user questions via retrieval + LLM
  → analytics/trend_analytics.py aggregates by date/product/topic
  → data/analytics/sentiment_trends.parquet
  → Dashboard pages read from FastAPI endpoints
  → alerts/alert_engine.py monitors for spikes, drops, surges
  → reports/report_generator.py produces PDF/Excel summaries
```

## Current State vs. Target

| Module                       | Status      | Notes                                                    |
|------------------------------|-------------|----------------------------------------------------------|
| **Data Collection**          | Partial     | Selenium Amazon scraper + RSS news scraper exist; no unified pipeline, no common schema |
| **Data Cleaning**            | Partial     | Basic cleaner exists; needs dedup, language filter, parquet output |
| **Sentiment Model**          | Implemented | RoBERTa (local) + Groq LLM (enhanced); needs clean abstraction layer |
| **Topic Modeling**           | Implemented | BERTopic + KeyBERT; needs pipeline integration |
| **RAG Pipeline**             | Implemented | ChromaDB + LangChain + Groq; works end-to-end |
| **Trend Analytics**          | Implemented | Regression, spike detection, forecasting; needs aggregation pipeline |
| **React Dashboards**         | Implemented | 11 pages; needs auth guards, consistent API usage |
| **Alerts**                   | Partial     | In-memory only, no persistence, no notification hooks |
| **Report Generation**        | Implemented | PDF + Excel; needs CLI interface and scheduled runs |
| **Tests**                    | Missing     | Only ad-hoc scripts; no pytest, no CI |
| **Deployment**               | Missing     | No Dockerfile, no docker-compose, no CI/CD |
| **Config Management**        | Partial     | .env exists; needs alerts.yml, centralized config |
| **Security**                 | Critical    | Hardcoded MongoDB credentials in 8 files, weak JWT secret, exposed API key |

## Key Gaps to Address

1. **Unified data pipeline** — No `pipelines/` orchestration layer connecting scrapers → cleaning → storage
2. **Structured data directories** — No `data/processed/`, `data/enriched/`, `data/analytics/`
3. **Clean model abstractions** — Sentiment and topic code scattered across `llm/`, `services/`
4. **Pipeline CLI** — No way to run `python -m pipelines.data_ingestion_pipeline` etc.
5. **Alert persistence** — Alerts lost on server restart
6. **Report CLI** — No `python -m reports.generate --period weekly`
7. **Tests** — Zero pytest tests; need test_data_pipeline, test_models, test_rag
8. **Evaluation** — No model evaluation metrics
9. **Docker** — No containerization
10. **Security hardening** — Credentials must move to .env exclusively
