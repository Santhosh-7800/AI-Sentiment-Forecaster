# TrendAI - AI-Powered Market Intelligence Platform

<div align="center">

![TrendAI Logo](https://img.shields.io/badge/TrendAI-v1.0.0-0dccf2?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.128+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18.2+-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![MongoDB](https://img.shields.io/badge/MongoDB-Latest-47A248?style=for-the-badge&logo=mongodb&logoColor=white)

**Predictive AI platform for real-time market sentiment analysis and trend forecasting**

[Features](#features) • [Installation](#installation) • [Usage](#usage) • [API Documentation](#api-documentation)

</div>

---

## 🌟 Features

### Core Functionality
- 🤖 **AI-Powered Sentiment Analysis** - Advanced NLP models for consumer emotion detection
- 📊 **Real-Time Market Tracking** - Live data from social media, news, and e-commerce
- 📈 **Trend Forecasting** - Predictive analytics with 90-day windows
- 🔐 **Secure Authentication** - JWT-based user authentication with MongoDB
- 🎨 **Dark/Light Mode** - Beautiful UI with seamless theme switching
- 📱 **Responsive Design** - Optimized for all devices

### Technology Stack

#### Backend
- **FastAPI** - Modern, fast web framework for Python
- **MongoDB** - NoSQL database for flexible data storage
- **BeautifulSoup & Selenium** - Web scraping engines
- **Transformers (HuggingFace)** - State-of-the-art NLP models
- **JWT Authentication** - Secure token-based auth

#### Frontend
- **React 18** - Modern UI library
- **Vite** - Next-generation frontend tooling
- **Tailwind CSS 4** - Utility-first CSS framework
- **Framer Motion** - Smooth animations
- **Lucide React** - Beautiful icon library

---

## 📁 Project Structure

```
.
├── backend/
│   ├── server.py              # Main FastAPI application (UPDATED)
│   ├── oauth2.py              # JWT token management
│   ├── schemas.py             # Pydantic models
│   ├── hashing.py             # Password hashing utilities
│   ├── requirements.txt       # Python dependencies
│   │
│   ├── routers/
│   │   └── authentication.py  # Auth endpoints (login/register)
│   │
│   ├── services/
│   │   └── user_service.py    # User database operations
│   │
│   ├── scraper/
│   │   ├── selenium_scraper.py  # Product review scraper
│   │   └── news_scraper.py      # News article scraper
│   │
│   ├── llm/
│   │   └── sentiment_engine.py  # AI sentiment analysis engine
│   │
│   ├── utils/
│   │   └── cleaner.py          # Text preprocessing utilities
│   │
│   └── output/
│       ├── results.csv         # Product sentiment results
│       └── news_results.csv    # News sentiment results
│
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── index.html
    │
    └── src/
        ├── App.jsx              # Main app with routing
        ├── main.jsx             # React entry point
        ├── index.css            # Global styles with theme support
        │
        ├── context/
        │   └── ThemeContext.jsx # Dark/Light mode provider (NEW)
        │
        ├── components/
        │   ├── Layout.jsx       # Page layout with navbar/footer
        │   ├── Sidebar.jsx      # Dashboard sidebar
        │   ├── DashboardLayout.jsx
        │   └── ThemeToggle.jsx  # Theme switcher component (NEW)
        │
        └── pages/
            ├── Landing.jsx      # Landing page
            ├── Login.jsx        # Login page (UPDATED)
            ├── Signup.jsx       # Registration page (UPDATED)
            ├── Dashboard.jsx    # Main dashboard
            ├── Sentiment.jsx    # Sentiment analysis view
            ├── MarketTrends.jsx # Market trends view
            ├── Reports.jsx      # Reports page
            ├── Settings.jsx     # User settings
            ├── HelpCenter.jsx   # Help & support
            └── AdminPanel.jsx   # Admin controls
```

---

## 🚀 Installation

### Prerequisites
- **Python 3.9+**
- **Node.js 16+** and npm
- **MongoDB** (running on localhost:27017)

### Backend Setup

1. **Navigate to backend directory:**
   ```powershell
   cd backend
   ```

2. **Create virtual environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Ensure MongoDB is running:**
   ```powershell
   # Start MongoDB service (if not already running)
   # mongod --version  # Verify installation
   ```

5. **Start the backend server:**
   ```powershell
   python server.py
   ```
   
   The API will be available at: `http://localhost:8000`
   - API Docs: `http://localhost:8000/docs`
   - Alternative Docs: `http://localhost:8000/redoc`

### Frontend Setup

1. **Navigate to frontend directory:**
   ```powershell
   cd frontend
   ```

2. **Install dependencies:**
   ```powershell
   npm install
   ```

3. **Start development server:**
   ```powershell
   npm run dev
   ```
   
   The app will be available at: `http://localhost:5173`

---

## 💻 Usage

### Running the Full Application

1. **Terminal 1 - Backend:**
   ```powershell
   cd backend
   python server.py
   ```

2. **Terminal 2 - Frontend:**
   ```powershell
   cd frontend
   npm run dev
   ```

3. **Access the application:**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Creating Your First Account

1. Navigate to http://localhost:5173
2. Click "Get Started" or "Sign Up"
3. Fill in your details:
   - First Name
   - Last Name
   - Email
   - Password (min 8 characters)
4. Click "Create Account"
5. Login with your credentials

### Theme Switching

- Click the **Sun/Moon icon** in the top-right corner
- Theme preference is saved in localStorage
- Both dark and light modes are fully optimized for readability

---

## 🔌 API Documentation

### Authentication Endpoints

#### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "firstname": "John",
  "lastname": "Doe",
  "email": "john@example.com",
  "password": "securepassword"
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### Scraping Endpoints

#### Scrape Products
```http
GET /api/scrape/products
Authorization: Bearer {token}
```

#### Scrape News
```http
GET /api/scrape/news
Authorization: Bearer {token}
```

### Data Retrieval Endpoints

#### Get Product Sentiments
```http
GET /api/products
Authorization: Bearer {token}
```

#### Get News Sentiments
```http
GET /api/news
Authorization: Bearer {token}
```

#### Health Check
```http
GET /api/health
```

---

## 🎨 Theme System

The application features a comprehensive dark/light mode system:

### Color Palette

| Element | Dark Mode | Light Mode |
|---------|-----------|------------|
| Primary | #0dccf2 | #0dccf2 |
| Background | #0a1014 | #ffffff |
| Surface | #1a2329 | #f8fafc |
| Text Primary | #f1f5f9 | #1e293b |
| Text Secondary | #94a3b8 | #64748b |
| Border | #334155 | #e2e8f0 |

### Theme Usage in Components

```jsx
import { useTheme } from '../context/ThemeContext';

function MyComponent() {
    const { theme, toggleTheme } = useTheme();
    
    return (
        <div className="bg-[var(--bg-primary)] text-[var(--text-primary)]">
            <button onClick={toggleTheme}>
                Toggle Theme
            </button>
        </div>
    );
}
```

---

## 🔒 Security Features

- **Password Hashing**: bcrypt with salt
- **JWT Tokens**: Secure authentication tokens
- **CORS Protection**: Configured for localhost only (production requires update)
- **Input Validation**: Pydantic schemas for all endpoints
- **MongoDB Security**: Connection timeout and error handling

---

## 📊 Database Schema

### Users Collection
```javascript
{
  "_id": ObjectId,
  "firstname": String,
  "lastname": String,
  "email": String (unique),
  "password": String (hashed)
}
```

### Product Results Collection
```javascript
{
  "category": String,
  "product_url": String,
  "review": String,
  "sentiment_label": String,
  "confidence_score": Number,
  "negative_percent": Number,
  "neutral_percent": Number,
  "positive_percent": Number
}
```

### News Results Collection
```javascript
{
  "platform": String,
  "keyword": String,
  "title": String,
  "description": String,
  "sentiment_label": String,
  "sentiment_score": Number,
  "published_date": String
}
```

---

## 🛠️ Development

### Building for Production

#### Frontend
```powershell
cd frontend
npm run build
```

#### Backend
The backend is production-ready. For deployment:
1. Update CORS origins in `server.py`
2. Configure production MongoDB connection
3. Set environment variables for secrets
4. Use production WSGI server (gunicorn/uvicorn)

---

## 🐛 Troubleshooting

### MongoDB Connection Failed
```
✗ MongoDB Connection Failed
```
**Solution:** Ensure MongoDB is running:
```powershell
# Check if MongoDB is running
mongo --version

# Start MongoDB service (Windows)
net start MongoDB
```

### Port Already in Use
**Backend (8000):**
```powershell
# Find and kill process using port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Frontend (5173):**
```powershell
# Find and kill process using port 5173
netstat -ano | findstr :5173
taskkill /PID <PID> /F
```

### Module Not Found Errors
**Backend:**
```powershell
pip install -r requirements.txt --force-reinstall
```

**Frontend:**
```powershell
rm -rf node_modules package-lock.json
npm install
```

---

## 📝 License

This project is for educational and commercial purposes.

---

## 👥 Contributors

- Development Team
- AI/ML Engineers
- Frontend Developers
- Backend Developers

---

## 🙏 Acknowledgments

- HuggingFace Transformers
- FastAPI Documentation
- React Community
- Tailwind CSS Team

---

<div align="center">

**Built with ❤️ using AI-first principles**

[⬆ Back to Top](#trendai---ai-powered-market-intelligence-platform)

</div>
