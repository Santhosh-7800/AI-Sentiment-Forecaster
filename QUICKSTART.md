# TrendAI - Quick Start Guide

## 🚀 Current Status

Your TrendAI application is now **RUNNING**!

### ✅ What's Working:
- ✅ **Backend Server**: Running on http://localhost:8000
- ✅ **Frontend App**: Running on http://localhost:5173
- ✅ **Dark/Light Mode**: Fully implemented and working
- ✅ **Beautiful UI**: Responsive design with smooth animations
- ✅ **Fixed Registration**: All form validation working
- ✅ **Professional Structure**: Clean, organized codebase

### ⚠️ What Needs MongoDB:
- ⚠️ **User Registration/Login**: Requires MongoDB to store users
- ⚠️ **Data Storage**: Product and news sentiment data

### 📌 Optional Features (Not Required for UI Testing):
- Scraping modules (selenium) - for product/news scraping
- Sentiment analysis (transformers) - for AI analysis

---

## 🎯 Quick Test Without MongoDB

You can still test the **entire UI and theme switching**:

1. **Open your browser**: http://localhost:5173
2. **Explore the beautiful landing page** ✨
3. **Test the theme toggle** (Sun/Moon icon in top-right) 🌙☀️
4. **Navigate to Signup/Login pages** - fully styled and responsive
5. **Check responsiveness** - resize browser window

---

## 💾 Setting Up MongoDB (For Full Functionality)

### Option 1: Install MongoDB Community Edition (Recommended)

#### Windows:
1. **Download MongoDB**:
   ```
   https://www.mongodb.com/try/download/community
   ```

2. **Install** (Use default settings)

3. **Start MongoDB Service**:
   ```powershell
   net start MongoDB
   ```

4. **Verify**:
   ```powershell
   mongo --version
   ```

#### OR Use MongoDB Compass (GUI):
- Download: https://www.mongodb.com/products/compass
- Install and run
- Connect to: `mongodb://localhost:27017`

### Option 2: Use MongoDB Atlas (Cloud - Free Tier)

1. **Sign up**: https://www.mongodb.com/cloud/atlas/register
2. **Create free cluster**
3. **Get connection string**
4. **Update `backend/server.py`**:
   ```python
   # Line ~50, replace:
   client = MongoClient("mongodb://localhost:27017")
   
   # With your Atlas connection:
   client = MongoClient("your-connection-string-here")
   ```

### Option 3: Docker (If you have Docker installed)

```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

---

## 🔄 After Installing MongoDB

1. **Restart the backend server**:
   - Press `CTRL+C` in backend terminal
   - Run: `python server.py`
   - You should see: `✓ MongoDB Connected Successfully`

2. **Test Registration**:
   - Go to: http://localhost:5173/signup
   - Fill in the form
   - Submit
   - You should get "Registration successful!"

3. **Test Login**:
   - Go to: http://localhost:5173/login
   - Use the credentials you just created
   - You should be redirected to the dashboard

---

## 🎨 Theme Features Showcase

### Dark Mode (Default)
- Deep dark background: `#0a1014`
- Cyan accents: `#0dccf2`
- Perfect for low-light environments
- Smooth gradients and shadows

### Light Mode
- Clean white background: `#ffffff`
- Same cyan accent for consistency
- Easy on the eyes in bright environments
- Professional look

### Toggle Button
- Top-right corner on all pages
- Sun icon (☀️) in dark mode → click for light
- Moon icon (🌙) in light mode → click for dark
- Smooth transition animation
- Preference saved in browser

---

## 📂 What We've Improved

### Backend Changes:
1. ✅ Created `server.py` - Professional FastAPI server
2. ✅ Fixed registration endpoint indentation
3. ✅ Added CORS middleware for frontend communication
4. ✅ Graceful error handling for optional modules
5. ✅ Health check endpoint
6. ✅ Comprehensive API documentation

### Frontend Changes:
1. ✅ Created `ThemeContext.jsx` - Global theme state
2. ✅ Created `ThemeToggle.jsx` - Beautiful toggle button
3. ✅ Updated all pages for theme support:
   - Login.jsx - Full theme support + loading states
   - Signup.jsx - Responsive forms + validation
   - Landing.jsx - Dynamic theme colors
   - Layout.jsx - Theme-aware navbar & footer
4. ✅ Updated `index.css` - CSS variables for themes
5. ✅ Updated `App.jsx` - Theme provider wrapper

### Documentation:
1. ✅ Created comprehensive `README.md`
2. ✅ Created this `QUICKSTART.md`
3. ✅ Added inline code comments

---

## 🎬 Theme Demo Script

1. **Start on Landing Page** (Dark Mode by default)
   - Notice the dark background with cyan highlights
   - Hover over buttons to see effects

2. **Click Theme Toggle** (top-right)
   - Watch the smooth transition to light mode
   - All text remains perfectly readable
   - Colors maintain professionalism

3. **Navigate to Signup**
   - Notice the beautiful form styling
   - Inputs have proper focus states
   - Theme-aware icons and borders

4. **Navigate to Login**
   - Similar beautiful design
   - Social login buttons styled for both themes
   - Gradient effects adapt to theme

5. **Toggle Theme Multiple Times**
   - Notice instant response
   - No layout shifts
   - Preference is remembered (localStorage)

---

## 🔧 Troubleshooting

### Frontend Won't Start
```powershell
cd frontend
rm -rf node_modules
npm install
npm run dev
```

### Backend Won't Start
```powershell
cd backend
pip install fastapi uvicorn pymongo passlib[bcrypt] python-jose[cryptography]
python server.py
```

### Port Already in Use
```powershell
# Backend (8000)
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Frontend (5173)
netstat -ano | findstr :5173
taskkill /PID <PID> /F
```

### Theme Not Switching
- Hard refresh: `CTRL + SHIFT + R`
- Clear localStorage: Console → `localStorage.clear()`
- Check console for errors: `F12` → Console tab

---

## 📱 Testing Responsive Design

### Desktop (1920x1080)
- Full navigation bar
- Side-by-side layouts
- Large typography

### Tablet (768x1024)
- Responsive grid
- Stacked sections
- Medium typography

### Mobile (375x667)
- Hamburger menu
- Single column
- Optimized spacing

---

## 🌟 Next Steps (Optional Enhancements)

### Install Scraping Modules:
```powershell
pip install selenium beautifulsoup4 webdriver-manager
```

### Install Sentiment Analysis:
```powershell
pip install transformers torch pandas
```

### Add More Features:
- Dashboard charts and graphs
- User profile settings
- Export data to CSV
- Email notifications
- Real-time WebSocket updates

---

## 📞 Support

If you encounter any issues:
1. Check this guide first
2. Review the main README.md
3. Check terminal outputs for errors
4. Test API at: http://localhost:8000/docs

---

## 🎉 Congratulations!

Your TrendAI application is now:
- ✨ Beautifully designed
- 🎨 Theme-ready (dark/light)
- 📱 Fully responsive
- 🔒 Secure (JWT auth ready)
- 📦 Professionally organized
- 🚀 Production-ready structure

**Enjoy exploring your new AI-powered platform!**
