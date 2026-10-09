# RAG Quick Start Guide

## 🚀 Get Started in 5 Steps

### Step 1: Install Dependencies (5 minutes)

```bash
cd backend
pip install -r rag_requirements.txt
```

This installs:
- ✅ LangChain (RAG framework)
- ✅ ChromaDB (vector database - free, local)
- ✅ Sentence Transformers (embeddings - free, local)
- ✅ OpenAI client (for GPT models)

---

### Step 2: Configure Environment (2 minutes)

1. **Copy the example file:**
```bash
cp .env.example .env
```

2. **Get your OpenAI API key:**
   - Visit: https://platform.openai.com/api-keys
   - Sign up or log in
   - Create new secret key
   - Copy the key

3. **Edit `.env` file and add your key:**
```env
OPENAI_API_KEY=sk-your-actual-api-key-here
```

The rest can stay as default! The free setup uses:
- HuggingFace embeddings (runs locally, free)
- ChromaDB vector store (local, free)
- OpenAI GPT-4o-mini (very cheap: ~$0.15 per 1M tokens)

---

### Step 3: Verify Setup (1 minute)

```bash
python scripts/setup_rag.py
```

This checks:
- ✅ All dependencies installed
- ✅ Environment configured
- ✅ RAG system initializes correctly

---

### Step 4: Index Your Data (2 minutes)

```bash
python scripts/index_data.py
```

This:
- Fetches reviews and news from MongoDB
- Chunks them into smaller pieces
- Creates embeddings
- Stores in vector database

**Note**: Make sure you have some data in MongoDB first (run your scrapers)

---

### Step 5: Start Using RAG! (immediate)

#### Option A: Test via Script
```bash
python scripts/test_rag.py
```

#### Option B: Start Server & Use API
```bash
python server.py
```

Then open: http://localhost:8000/docs

Navigate to **RAG** section and try queries!

#### Option C: Use Python Code
```python
from rag.rag_service import get_rag_engine

engine = get_rag_engine()

result = engine.query("What do customers like about electronics?")
print(result['answer'])
```

---

## 📝 Example Usage

### Via API (cURL)

```bash
# Login first
curl -X POST http://localhost:8000/api/auth/login \
  -d "username=your_email&password=your_pass"

# Save the token, then query:
curl -X POST http://localhost:8000/api/rag/query \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the top complaints about electronics?",
    "return_sources": true
  }'
```

### Via Python Requests

```python
import requests

# Login
login = requests.post(
    "http://localhost:8000/api/api/auth/login",
    data={"username": "user@example.com", "password": "password"}
)
token = login.json()["access_token"]

# Query RAG
response = requests.post(
    "http://localhost:8000/api/rag/query",
    headers={"Authorization": f"Bearer {token}"},
    json={"question": "What's trending in consumer sentiment?"}
)

print(response.json()["answer"])
```

### Via Frontend (React)

```javascript
const queryRAG = async (question) => {
  const token = localStorage.getItem('token');
  const response = await fetch('http://localhost:8000/api/rag/query', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ question })
  });
  return response.json();
};

// Use it
const result = await queryRAG("What do customers think about our products?");
console.log(result.answer);
```

---

## 🎯 Available Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/rag/query` | Ask natural language questions |
| `POST /api/rag/insights` | Get contextual insights |
| `GET /api/rag/sentiment-summary` | Get sentiment summary |
| `GET /api/rag/trending-topics` | Get trending topics |
| `POST /api/rag/compare-categories` | Compare categories |
| `POST /api/rag/index/mongodb` | Index documents |
| `GET /api/rag/stats` | Get system stats |

---

## 💡 Example Questions You Can Ask

- "What are customers saying about electronics?"
- "What's the overall sentiment for our products?"
- "What are the most common complaints?"
- "Which category has the best reviews?"
- "What are trending topics in consumer feedback?"
- "How do electronics compare to clothes in sentiment?"
- "What do people like most about our essentials?"
- "Are there any recurring issues customers mention?"

---

## ⚠️ Troubleshooting

### "RAG system not initialized"
**Fix**: Check your `.env` file has `OPENAI_API_KEY` set

### "No documents indexed"
**Fix**: Run `python scripts/index_data.py` first

### "Connection refused"
**Fix**: Start the server with `python server.py`

### "Rate limit exceeded"
**Fix**: You're out of OpenAI credits. Add payment method or wait.

### Slow first query
**Normal**: First query loads models, subsequent ones are faster

---

## 💰 Cost Estimate

**Development (100 queries/day):**
- Embeddings: FREE (runs locally)
- Vector Store: FREE (ChromaDB local)
- LLM (GPT-4o-mini): ~$0.50/month

**Production (1000 queries/day):**
- Embeddings: FREE
- Vector Store: $0-70/month (Pinecone free tier or paid)
- LLM: ~$5/month

---

## 🎓 What Did You Just Build?

✅ **RAG Pipeline** - Retrieves relevant context before answering  
✅ **Vector Search** - Semantic search through your data  
✅ **Contextual AI** - Answers grounded in your actual data  
✅ **API Endpoints** - Ready to integrate with frontend  
✅ **Scalable Architecture** - Can handle thousands of documents  

---

## 📚 Next Steps

1. **Index more data** - Run scrapers to collect more reviews/news
2. **Customize prompts** - Edit prompts in `rag/query_engine.py`
3. **Build frontend** - Create UI components for RAG queries
4. **Add caching** - Cache frequent queries to reduce costs
5. **Deploy** - Move to production with Pinecone

---

Need help? Check [RAG_IMPLEMENTATION_GUIDE.md](RAG_IMPLEMENTATION_GUIDE.md) for detailed docs!

🎉 Happy querying!
