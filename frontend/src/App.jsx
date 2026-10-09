import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Dashboard from './pages/Dashboard';
import MarketTrends from './pages/MarketTrends';
import Sentiment from './pages/Sentiment';
import Analytics from './pages/Analytics';
import Reports from './pages/Reports';
import Settings from './pages/Settings';
import HelpCenter from './pages/HelpCenter';
import AdminPanel from './pages/AdminPanel';
import TrendingProducts from './pages/TrendingProducts';
import ForgotPassword from './pages/ForgotPassword';

function App() {
    return (
        <ThemeProvider>
            <Router>
                <Routes>
                    <Route path="/" element={<Landing />} />
                    <Route path="/login" element={<Login />} />
                    <Route path="/signup" element={<Signup />} />
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/trending-products" element={<TrendingProducts />} />
                    <Route path="/market-trends" element={<MarketTrends />} />
                    <Route path="/sentiment" element={<Sentiment />} />
                    <Route path="/analytics" element={<Analytics />} />
                    <Route path="/reports" element={<Reports />} />
                    <Route path="/settings" element={<Settings />} />
                    <Route path="/help" element={<HelpCenter />} />
                    <Route path="/admin" element={<AdminPanel />} />
                    <Route path="/forgot-password" element={<ForgotPassword />} />
                </Routes>
            </Router>
        </ThemeProvider>
    );
}

export default App;
