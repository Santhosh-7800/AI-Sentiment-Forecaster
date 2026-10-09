# RAG Implementation Guide

## 🎯 Overview

This guide will help you implement RAG (Retrieval-Augmented Generation) into your AI-Powered Market Trend & Consumer Sentiment Forecaster project.

## 📋 Table of Contents

1. [What is RAG?](#what-is-rag)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Implementation Steps](#implementation-steps)
6. [API Usage](#api-usage)
7. [Testing](#testing)
8. [Deployment Considerations](#deployment-considerations)

---

## 🤔 What is RAG?

**RAG (Retrieval-Augmented Generation)** combines the power of:
- **Vector Search**: Finds relevant context from your data
- **LLM Generation**: Uses that context to generate intelligent, data-driven answers

For your project, RAG enables:
- ✅ Contextual answers about consumer sentiment
- ✅ Trend analysis based on actual review/news data
- ✅ Personalized insights for specific categories/products
- ✅ Reduced hallucinations (answers grounded in real data)

---

## 🏗️ Architecture

```
User Query
    ↓
[1] Query Processing
    ↓
[2] Vector Search (Retrieve relevant documents)
    ↓
[3] Context Building
    ↓
[4] LLM Generation (Answer with context)
    ↓
Response + Sources
```

### Components Created:

1. **`rag/config.py`** - Configuration management
2. **`rag/document_processor.py`** - Document chunking & preparation
3. **`rag/vector_store.py`** - Vector database operations
4. **`rag/query_engine.py`** - RAG query processing
5. **`rag/rag_service.py`** - Service initialization
6. **`routers/rag_routes.py`** - FastAPI endpoints

---

## 📦 Installation

### Step 1: Install RAG Dependencies

```bash
cd backend
pip install -r rag_requirements.txt
```

**This installs:**
- LangChain framework
- ChromaDB (vector database)
- Sentence Transformers (embeddings)
- OpenAI client (optional, for GPT models)

### Step 2: Choose Your Setup

#### Option A: Free Setup (Recommended for Development)
- **Embeddings**: HuggingFace (sentence-transformers)
- **Vector Store**: ChromaDB (local)
- **LLM**: OpenAI GPT-4o-mini (requires API key)

#### Option B: Cloud Setup
- **Embeddings**: OpenAI
- **Vector Store**: Pinecone
- **LLM**: OpenAI GPT-4

#### Option C: Fully Local Setup
- **Embeddings**: HuggingFace
- **Vector Store**: FAISS
- **LLM**: Ollama (requires local installation)

---

## ⚙️ Configuration

### Step 1: Create `.env` File

```bash
cd backend
cp .env.example .env
```

### Step 2: Configure Environment Variables

**For Free Setup (Recommended):**

```env
# LLM Configuration
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o-mini

# Embeddings (Free, runs locally)
EMBEDDING_PROVIDER=huggingface
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

# Vector Store (Free, local)
VECTOR_STORE=chromadb
CHROMA_PERSIST_DIR=./data/chromadb
CHROMA_COLLECTION_NAME=market_trends

# RAG Settings
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
RETRIEVAL_TOP_K=5
```

### Step 3: Get OpenAI API Key

1. Visit: https://platform.openai.com/api-keys
2. Create an account or sign in
3. Click "Create new secret key"
4. Copy the key and paste it in your `.env` file

**Cost**: GPT-4o-mini costs ~$0.15 per 1M input tokens (very cheap!)

---

## 🚀 Implementation Steps

### Step 1: Update `server.py` to Include RAG Routes

Add this to [server.py](server.py):

```python
# Import RAG router
try:
    from routers import rag_routes
    app.include_router(rag_routes.router)
    print("✓ RAG routes loaded")
except ImportError as e:
    print(f"⚠️  RAG routes not available: {e}")
    print("  Install RAG dependencies: pip install -r rag_requirements.txt")
```

### Step 2: Initialize RAG on Startup (Optional)

Add to [server.py](server.py) after app initialization:

```python
from rag.rag_service import initialize_rag_engine

@app.on_event("startup")
async def startup_event():
    """Initialize RAG engine on startup"""
    try:
        initialize_rag_engine()
        print("✓ RAG Engine ready")
    except Exception as e:
        print(f"⚠️  RAG initialization failed: {e}")
        print("  RAG features will be unavailable")
```

### Step 3: Start the Server

```bash
cd backend
python server.py
```

### Step 4: Index Your Data

**Option A: Via API (Recommended)**

```bash
# Get authentication token first (login via your app)
# Then index MongoDB documents:

curl -X POST "http://localhost:8000/api/rag/index/mongodb" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "mongodb",
    "doc_type": "all",
    "limit": 100
  }'
```

**Option B: Via Python Script**

Create [scripts/index_data.py](scripts/index_data.py):

```python
from rag.rag_service import initialize_rag_engine
from rag.document_processor import DocumentProcessor
from pymongo import MongoClient

# Initialize RAG
rag_engine = initialize_rag_engine()
processor = DocumentProcessor()

# Connect to MongoDB
client = MongoClient("your_mongodb_connection_string")
db = client["ai_project_db"]

# Index product reviews
reviews = list(db["product_results"].find().limit(100))
review_chunks = processor.process_batch_from_mongodb(reviews, "review")

# Index news articles
news = list(db["news_results"].find().limit(100))
news_chunks = processor.process_batch_from_mongodb(news, "news")

# Add to vector store
all_chunks = review_chunks + news_chunks
result = rag_engine.index_documents(all_chunks)

print(f"✓ Indexed {result['indexed_count']} documents")
```

---

## 🔌 API Usage

### 1. Query RAG System

**Endpoint**: `POST /api/rag/query`

**Request**:
```json
{
  "question": "What are customers saying about electronics?",
  "category": "electronics",
  "sentiment": "Positive",
  "return_sources": true
}
```

**Response**:
```json
{
  "question": "What are customers saying about electronics?",
  "answer": "Based on the reviews, customers have positive feedback about electronics, particularly praising...",
  "sources": [
    {
      "content": "Great product! The quality is excellent...",
      "metadata": {
        "category": "electronics",
        "sentiment": "Positive",
        "confidence": 0.95
      }
    }
  ],
  "source_count": 5,
  "success": true
}
```

### 2. Get Contextual Insights

**Endpoint**: `POST /api/rag/insights`

```json
{
  "query": "smartphone battery complaints",
  "context_type": "reviews"
}
```

### 3. Get Sentiment Summary

**Endpoint**: `GET /api/rag/sentiment-summary?category=electronics`

Returns sentiment trends and statistics for the category.

### 4. Get Trending Topics

**Endpoint**: `GET /api/rag/trending-topics?limit=5`

Returns top trending topics from consumer discussions.

### 5. Compare Categories

**Endpoint**: `POST /api/rag/compare-categories`

```json
{
  "categories": ["electronics", "clothes", "essentials"]
}
```

### 6. Get System Stats

**Endpoint**: `GET /api/rag/stats`

Returns RAG system configuration and statistics.

---

## 🧪 Testing

### Test via Swagger UI

1. Start server: `python server.py`
2. Open: http://localhost:8000/docs
3. Navigate to "RAG" section
4. Try the endpoints with authentication token

### Test via Python

```python
import requests

# Login first
login_response = requests.post(
    "http://localhost:8000/api/auth/login",
    data={"username": "your_email", "password": "your_password"}
)
token = login_response.json()["access_token"]

# Query RAG
headers = {"Authorization": f"Bearer {token}"}
response = requests.post(
    "http://localhost:8000/api/rag/query",
    headers=headers,
    json={
        "question": "What do customers like about electronics?",
        "return_sources": True
    }
)

print(response.json())
```

### Test via cURL

```bash
# Get token
TOKEN="your_access_token"

# Query
curl -X POST "http://localhost:8000/api/rag/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the trending products?"}'
```

---

## 🎨 Frontend Integration

### Add RAG Query Component

Create [frontend/src/components/RAGQuery.jsx](frontend/src/components/RAGQuery.jsx):

```jsx
import { useState } from 'react';
import axios from 'axios';

export default function RAGQuery() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleQuery = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        'http://localhost:8000/api/rag/query',
        { question, return_sources: true },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setAnswer(response.data);
    } catch (error) {
      console.error('Query failed:', error);
      alert('Failed to get answer');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rag-query">
      <h2>Ask About Market Trends</h2>
      <textarea
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Ask a question about consumer sentiment or trends..."
        rows={3}
      />
      <button onClick={handleQuery} disabled={loading}>
        {loading ? 'Searching...' : 'Get Answer'}
      </button>

      {answer && (
        <div className="answer">
          <h3>Answer:</h3>
          <p>{answer.answer}</p>
          
          {answer.sources && (
            <details>
              <summary>View Sources ({answer.source_count})</summary>
              {answer.sources.map((source, idx) => (
                <div key={idx} className="source">
                  <p>{source.content}</p>
                  <small>
                    Category: {source.metadata.category} | 
                    Sentiment: {source.metadata.sentiment}
                  </small>
                </div>
              ))}
            </details>
          )}
        </div>
      )}
    </div>
  );
}
```

---

## 📊 Deployment Considerations

### For Production:

1. **Use Pinecone or Managed Vector DB**
   - ChromaDB is great for dev, but Pinecone is better for production
   - Pinecone offers free tier: 1 index, 100K vectors

2. **Rate Limiting**
   - Add rate limiting to RAG endpoints (expensive LLM calls)

3. **Caching**
   - Cache frequent queries to reduce API costs
   - Use Redis for query result caching

4. **Monitor Costs**
   - Track OpenAI API usage
   - Set spending limits in OpenAI dashboard

5. **Background Indexing**
   - Index new documents in background tasks
   - Use Celery or similar for async processing

6. **Security**
   - Validate and sanitize all user inputs
   - Implement proper authentication/authorization
   - Use environment variables for all secrets

---

## 🎯 Milestone Integration

### Milestone 3 (Weeks 5-6): RAG & Dashboards

✅ **Tasks Completed:**
- LangChain + Vector DB integration
- Document processing pipeline
- RAG query engine
- API endpoints

📝 **Remaining Tasks:**
- Index all MongoDB data
- Build frontend RAG components
- Create insights dashboard
- Integrate with existing visualizations

### Next Steps:

1. **Week 5**: Complete data indexing, test RAG queries
2. **Week 6**: Build dashboard with RAG integration
3. **Milestone Evaluation**: Demo contextual insights and trend analysis

---

## 💡 Tips & Best Practices

1. **Start Small**: Index 100-500 documents first, then scale up
2. **Monitor Performance**: Track query latency and accuracy
3. **Iterate Prompts**: Customize prompts in `query_engine.py` for better results
4. **Use Filters**: Leverage metadata filters for targeted insights
5. **Test Thoroughly**: Validate answers against source data

---

## 🆘 Troubleshooting

### Issue: "RAG system not initialized"
- **Solution**: Check `.env` file, ensure OPENAI_API_KEY is set
- Run: `python -c "from rag.rag_service import initialize_rag_engine; initialize_rag_engine()"`

### Issue: "No relevant documents found"
- **Solution**: Index documents first using `/api/rag/index/mongodb`

### Issue: OpenAI rate limits
- **Solution**: Reduce RETRIEVAL_TOP_K, use GPT-3.5-turbo, or add retry logic

### Issue: Slow queries
- **Solution**: Reduce chunk_size, use FAISS instead of ChromaDB, cache results

---

## 📚 Additional Resources

- **LangChain Docs**: https://python.langchain.com/docs/
- **ChromaDB Docs**: https://docs.trychroma.com/
- **OpenAI API**: https://platform.openai.com/docs/
- **RAG Concepts**: https://www.pinecone.io/learn/retrieval-augmented-generation/

---

## ✅ Checklist

- [ ] Install dependencies (`pip install -r rag_requirements.txt`)
- [ ] Create `.env` file with API keys
- [ ] Update `server.py` with RAG router
- [ ] Start server and verify RAG endpoints in Swagger
- [ ] Index sample documents
- [ ] Test RAG queries via API
- [ ] Build frontend components
- [ ] Deploy to production

---

**Need Help?** Check the code comments or reach out to your team!

Good luck with your RAG implementation! 🚀
