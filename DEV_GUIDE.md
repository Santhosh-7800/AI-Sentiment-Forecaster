# Developer Guide — TrendAI

## Repository Structure

```
TrendAI/
├── backend/                    # FastAPI backend server
│   ├── server.py               # Main app entry point (routes, CORS, startup)
│   ├── database.py             # MongoDB connection
│   ├── oauth2.py               # JWT auth
│   ├── schemas.py              # Pydantic models
│   ├── hashing.py              # Password hashing (bcrypt)
│   ├── routers/
│   │   ├── authentication.py   # /api/auth/login, /api/auth/register
│   │   ├── analytics_routes.py # /api/analytics/* (14 endpoints)
│   │   └── rag_routes.py       # /api/rag/* (8 endpoints)
│   ├── rag/                    # RAG system (LangChain + ChromaDB/Pinecone)
│   │   ├── config.py           # RAGConfig from .env
│   │   ├── document_processor.py # Chunking logic
│   │   ├── query_engine.py     # QA chain
│   │   ├── rag_service.py      # Singleton initializer
│   │   └── vector_store.py     # ChromaDB/Pinecone/FAISS abstraction
│   ├── services/
│   │   ├── realtime_analysis.py  # Real-time product analyzer
│   │   ├── enhanced_sentiment.py # Aspect-based sentiment
│   │   ├── topic_modeling.py     # BERTopic service
│   │   ├── trend_analytics.py    # Regression, forecasting
│   │   ├── alerts.py             # In-memory alert system
│   │   ├── report_generation.py  # PDF + Excel reports
│   │   ├── report_service.py     # Simple CSV-based reports
│   │   ├── csv_fetcher.py        # Local CSV data loader
│   │   ├── api_budget.py         # API quota manager
│   │   └── user_service.py       # User CRUD
│   ├── scraper/
│   │   ├── selenium_scraper.py   # Amazon review scraper
│   │   └── news_scraper.py       # Google News RSS scraper
│   ├── llm/
│   │   ├── sentiment_engine.py   # RoBERTa sentiment
│   │   └── topic_engine.py       # KeyBERT keywords
│   ├── scripts/                  # Utility scripts (DB, RAG indexing)
│   └── output/                   # CSV data files
│
├── frontend/                   # React + Vite + Tailwind CSS
│   ├── src/
│   │   ├── App.jsx             # Routes (11 pages)
│   │   ├── pages/              # Dashboard, Sentiment, MarketTrends, etc.
│   │   ├── components/         # Layout, Sidebar, ThemeToggle
│   │   ├── context/            # ThemeContext (dark mode)
│   │   └── lib/                # apiFetch(), sentiment utils
│   └── vite.config.js          # Dev server + API proxy
│
├── data_collection/            # [NEW] Data collection & normalization
│   └── collectors.py           # CSV ingestors, scrapers, common schema
│
├── pipelines/                  # [NEW] Orchestration pipelines
│   ├── data_ingestion_pipeline.py   # CSV → cleaned parquet
│   ├── sentiment_topic_pipeline.py  # processed → enriched (sentiment + topics)
│   ├── rag_index_pipeline.py        # enriched → vector store
│   └── analytics_pipeline.py        # enriched → aggregated analytics
│
├── models/                     # [NEW] Clean ML model abstractions
│   ├── sentiment_model.py      # RoBERTa sentiment (5-class, -1 to 1 score)
│   └── topic_model.py          # KeyBERT/BERTopic topic extraction
│
├── alerts/                     # [NEW] Alert engine with YAML config
│   └── alert_engine.py         # Anomaly detection, log + notify
│
├── reports/                    # [NEW] Report generation CLI
│   └── generate.py             # PDF + Excel reports from analytics
│
├── evaluation/                 # [NEW] Model evaluation
│   └── evaluate_models.py      # Distribution checks, consistency metrics
│
├── tests/                      # [NEW] Pytest test suite
│   ├── test_data_pipeline.py   # Data pipeline tests
│   └── test_models.py          # Sentiment + topic model tests
│
├── config/                     # [NEW] Configuration files
│   └── alerts.yml              # Alert thresholds, notification settings
│
├── data/                       # [NEW] Structured data directories
│   ├── processed/              # Cleaned data (parquet)
│   ├── enriched/               # Sentiment + topic enriched data
│   └── analytics/              # Aggregated analytics
│
├── output/                     # Raw CSV data (your existing extractions)
├── logs/                       # Alert logs
│
├── ARCHITECTURE_OVERVIEW.md    # System design document
├── DEV_GUIDE.md                # This file
├── Dockerfile                  # Backend container
├── docker-compose.yml          # Full stack orchestration
└── .env.example                # Environment variable template

```

## How Each Pipeline Connects

```
output/*.csv (your existing data)
    │
    ▼
[1] python -m pipelines.data_ingestion_pipeline
    │  Reads all CSVs, normalizes to common schema, deduplicates
    │  Output: data/processed/all_data.parquet
    │
    ▼
[2] python -m pipelines.sentiment_topic_pipeline
    │  Loads processed data, runs RoBERTa sentiment + KeyBERT topics
    │  Output: data/enriched/enriched_latest.parquet
    │
    ▼
[3] python -m pipelines.rag_index_pipeline
    │  Chunks enriched docs, embeds, upserts into ChromaDB
    │  Output: backend/data/chromadb/ (vector store)
    │
    ▼
[4] python -m pipelines.analytics_pipeline
    │  Aggregates by product, topic, date. Computes stats & trends
    │  Output: data/analytics/*.parquet, summary_stats.json
    │
    ▼
[5] cd backend && uvicorn server:app --reload
    │  FastAPI serves dashboards API, RAG queries, analytics endpoints
    │
    ▼
[6] cd frontend && npm run dev
    │  React dashboard at http://localhost:5173
    │
    ▼
[7] python -m alerts.alert_engine --check-once
    │  Detect anomalies, log to logs/alerts.log
    │
    ▼
[8] python -m reports.generate --period weekly
       Generate PDF + Excel reports in reports/output/
```

## Step-by-Step Setup

### 1. Prerequisites

- Python 3.10+
- Node.js 18+
- MongoDB (local or Atlas)
- Git

### 2. Clone and Setup Environment

```bash
git clone https://github.com/Diksha901/AI_Sentiment_Forecaster.git
cd AI_Sentiment_Forecaster

# Create Python virtual environment
python -m venv venv
source venv/bin/activate    # Linux/Mac
# venv\Scripts\activate     # Windows

# Install Python dependencies
pip install -r backend/requirements.txt
pip install -r backend/rag_requirements.txt
pip install pyarrow pyyaml keybert pytest openpyxl reportlab

# Install frontend dependencies
cd frontend && npm install && cd ..
```

### 3. Configure Environment Variables

```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your actual API keys
```

Required variables:
| Variable | Description | Where to get it |
|----------|-------------|-----------------|
| `GROQ_API_KEY` | Groq LLM API key (free tier) | https://console.groq.com |
| `MONGODB_URL` | MongoDB connection string | MongoDB Atlas or local |
| `JWT_SECRET_KEY` | Random secret for JWT tokens | Generate with `openssl rand -hex 32` |
| `NEWS_API_KEY` | NewsAPI key (optional) | https://newsapi.org |

### 4. Run Data Ingestion

```bash
# Ingest all existing CSVs from output/ into structured parquet
python -m pipelines.data_ingestion_pipeline
# Output: data/processed/all_data.parquet
```

### 5. Run Sentiment & Topic Modeling

```bash
# Enrich with sentiment scores and topic labels
python -m pipelines.sentiment_topic_pipeline
# Output: data/enriched/enriched_latest.parquet

# Evaluate model quality
python -m evaluation.evaluate_models
```

### 6. Build RAG Index

```bash
# Index enriched data into ChromaDB vector store
python -m pipelines.rag_index_pipeline
```

### 7. Generate Analytics

```bash
# Aggregate trends, product comparisons, topic stats
python -m pipelines.analytics_pipeline
# Output: data/analytics/summary_stats.json, *.parquet
```

### 8. Start Backend Server

```bash
cd backend
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
# API docs: http://localhost:8000/docs
```

### 9. Start Frontend

```bash
cd frontend
npm run dev
# Dashboard: http://localhost:5173
```

### 10. Run Alerts

```bash
# One-time check
python -m alerts.alert_engine --check-once

# Continuous monitoring (checks every hour)
python -m alerts.alert_engine --interval 3600
```

### 11. Generate Reports

```bash
# Weekly PDF + Excel report
python -m reports.generate --period weekly

# Monthly PDF only
python -m reports.generate --period monthly --format pdf

# Product-specific report
python -m reports.generate --period weekly --product "electronics"
# Output: reports/output/YYYY-MM-DD_weekly_report.pdf/.xlsx
```

### 12. Run Tests

```bash
pytest tests/ -v
```

## Docker Deployment

```bash
# Build and start all services
docker-compose up --build

# Services:
#   backend:  http://localhost:8000
#   frontend: http://localhost:5173
#   mongodb:  localhost:27017
#   alerts:   background worker
```

## API Endpoints Reference

### Authentication
- `POST /api/auth/register` — Create account
- `POST /api/auth/login` — Get JWT token

### Real-time Analysis
- `POST /api/realtime/analyze` — Analyze product (auth required)
- `GET /api/realtime/budget` — API budget status

### RAG
- `POST /api/rag/query` — Ask questions about data
- `POST /api/rag/insights` — Get category insights
- `GET /api/rag/sentiment-summary` — Overall sentiment summary
- `GET /api/rag/trending-topics` — Current trending topics
- `POST /api/rag/compare-categories` — Compare product categories
- `POST /api/rag/index/mongodb` — Re-index data from MongoDB

### Analytics
- `POST /api/analytics/enhanced-sentiment` — Enhanced sentiment analysis
- `POST /api/analytics/batch-sentiment` — Batch sentiment
- `POST /api/analytics/topics/extract` — Extract topics
- `POST /api/analytics/trends/analyze` — Trend analysis
- `POST /api/analytics/trends/spikes` — Spike detection
- `GET /api/analytics/alerts/active` — Active alerts
- `POST /api/analytics/reports/generate` — Generate report

### Admin
- `GET /api/stats` — System statistics
- `GET /api/health` — Health check
- `GET /api/admin/users` — User list (auth required)

## Milestone Checklist

### Milestone 1 (Weeks 1-2): Data Pipeline
- [x] Data collection layer (CSV ingestors + scraper wrappers)
- [x] Cleaning and normalization (common schema)
- [x] `data/processed/` structured storage
- [x] `tests/test_data_pipeline.py` (6+ unit tests)

### Milestone 2 (Weeks 3-4): ML Models
- [x] Sentiment model abstraction (`models/sentiment_model.py`)
- [x] Topic model abstraction (`models/topic_model.py`)
- [x] Enrichment pipeline (`pipelines/sentiment_topic_pipeline.py`)
- [x] `data/enriched/` output
- [x] Evaluation script (`evaluation/evaluate_models.py`)
- [x] `tests/test_models.py` (10+ unit tests)

### Milestone 3 (Weeks 5-6): RAG + Dashboards
- [x] RAG pipeline integrated (ChromaDB + LangChain + Groq)
- [x] RAG indexing pipeline from enriched data
- [x] React dashboards running locally (11 pages)
- [x] Analytics aggregation pipeline

### Milestone 4 (Weeks 7-8): Alerts + Reports + Deployment
- [x] Alert engine with YAML config
- [x] PDF + Excel report generation
- [x] Report CLI (`python -m reports.generate`)
- [x] Dockerfile + docker-compose.yml
- [x] This DEV_GUIDE.md
