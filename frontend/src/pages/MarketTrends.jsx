import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Download, ChevronRight, TrendingUp, TrendingDown, Globe, Zap, Loader2, Search } from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';
import { apiFetch, apiFetchJSON, exportAsCsv } from '../lib/api';
import { sentimentBreakdown } from '../lib/sentiment';

// Predefined keywords with categories
const PREDEFINED_KEYWORDS = {
    'Tech': ['iPhone', 'Samsung', 'Pixel', 'MacBook', 'iPad', 'Apple', 'Google', 'Microsoft', 'laptop', 'smartphone', 'tablet', 'smartwatch'],
    'E-commerce': ['Amazon', 'Flipkart', 'Myntra', 'Ajio', 'Snapdeal', 'Meesho', 'Nykaa', 'Blinkit', 'Swiggy'],
    'Brands': ['Nike', 'Adidas', 'Puma', 'Gucci', 'Zara', 'H&M', 'UNIQLO', 'Forever 21', 'ASOS'],
    'Home & Living': ['Ikea', 'Godrej', 'Furniture', 'Mattress', 'Appliances', 'AC', 'Microwave', 'Refrigerator'],
    'Fashion': ['Clothing', 'Shoes', 'Watches', 'Bags', 'Accessories', 'Dress', 'Jacket', 'Jeans'],
    'Food & Beverage': ['Starbucks', 'Dominos', 'McDonald\'s', 'KFC', 'Coca Cola', 'Pepsi', 'Coffee', 'Pizza'],
};

const MarketTrends = () => {
    const navigate = useNavigate();
    const [newsData, setNewsData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [sentiment, setSentiment] = useState({ positive: 0, negative: 0, neutral: 0, total: 0 });
    const [keywords, setKeywords] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [showSuggestions, setShowSuggestions] = useState(false);
    const [filteredSuggestions, setFilteredSuggestions] = useState([]);
    const [insights, setInsights] = useState([]);
    const [llmProvider, setLlmProvider] = useState('auto');
    const [error, setError] = useState('');

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token) { navigate('/login'); return; }
        fetchNews();
    }, []);

    // Handle search input and show suggestions
    useEffect(() => {
        if (searchQuery.trim()) {
            const query = searchQuery.toLowerCase();
            const suggestions = [];

            Object.entries(PREDEFINED_KEYWORDS).forEach(([category, kws]) => {
                const matches = kws.filter(kw => kw.toLowerCase().includes(query));
                matches.forEach(kw => {
                    suggestions.push({ name: kw, category });
                });
            });

            setFilteredSuggestions(suggestions.slice(0, 8));
            setShowSuggestions(suggestions.length > 0);
        } else {
            setShowSuggestions(false);
            setFilteredSuggestions([]);
        }
    }, [searchQuery]);

    const fetchNews = async () => {
        try {
            setLoading(true);
            setError('');
            const res = await apiFetch('/api/news');
            if (!res.ok) throw new Error('Failed to fetch news');
            const result = await res.json();
            const data = result.data || [];

            const breakdown = sentimentBreakdown(data);
            const pos = breakdown.Positive;
            const neg = breakdown.Negative;
            const neu = breakdown.Neutral;
            const total = breakdown.total;
            setSentiment({
                positive: total > 0 ? Math.round((pos / total) * 100) : 0,
                negative: total > 0 ? Math.round((neg / total) * 100) : 0,
                neutral: total > 0 ? Math.round((neu / total) * 100) : 0,
                total,
            });

            // Count keyword mentions
            const kwCount = {};
            data.forEach(n => {
                const kw = n.keyword || n.platform || 'other';
                kwCount[kw] = (kwCount[kw] || 0) + 1;
            });
            const sorted = Object.entries(kwCount)
                .sort((a, b) => b[1] - a[1])
                .map(([kw, count], idx) => ({
                    rank: String(idx + 1).padStart(2, '0'),
                    name: kw.charAt(0).toUpperCase() + kw.slice(1),
                    cat: 'News Keyword',
                    val: Math.min(Math.round((count / total) * 100 * 3), 100),
                    growth: count,
                }));
            setKeywords(sorted.slice(0, 8)); // Show more keywords
            setNewsData(data.slice(0, 10));
            setInsights([]);
        } catch (e) {
            console.error(e);
            setError(e.message || 'Unable to load market data.');
        } finally {
            setLoading(false);
        }
    };

    const runRealtimeSearch = async (inputValue) => {
        const query = (inputValue || searchQuery || '').trim();
        if (!query) {
            return;
        }

        try {
            setLoading(true);
            setError('');
            setShowSuggestions(false);

            const result = await apiFetchJSON('/api/realtime/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    product: query,
                    max_articles: 25,
                    force_refresh: true,
                    llm_provider: llmProvider,
                }),
            });

            const breakdown = result.sentiment_breakdown || {};
            const pos = Number(breakdown.positive || 0);
            const neg = Number(breakdown.negative || 0);
            const neu = Number(breakdown.neutral || 0);
            const total = Number(result.article_count || (pos + neg + neu));

            setSentiment({
                positive: total > 0 ? Math.round((pos / total) * 100) : 0,
                negative: total > 0 ? Math.round((neg / total) * 100) : 0,
                neutral: total > 0 ? Math.round((neu / total) * 100) : 0,
                total,
            });

            const articles = Array.isArray(result.top_articles) ? result.top_articles : [];
            setNewsData(articles.slice(0, 10));

            const kwCount = {};
            articles.forEach((item) => {
                const kw = item.keyword || item.platform || query;
                kwCount[kw] = (kwCount[kw] || 0) + 1;
            });
            const sorted = Object.entries(kwCount)
                .sort((a, b) => b[1] - a[1])
                .map(([kw, count], idx) => ({
                    rank: String(idx + 1).padStart(2, '0'),
                    name: kw.charAt(0).toUpperCase() + kw.slice(1),
                    cat: 'Realtime Keyword',
                    val: total > 0 ? Math.min(Math.round((count / total) * 100 * 2), 100) : 0,
                    growth: count,
                }));
            setKeywords(sorted.slice(0, 8));

            setInsights(Array.isArray(result.insights) ? result.insights : []);
            setSearchQuery(query);
        } catch (e) {
            console.error(e);
            setError(e.message || 'Realtime analysis failed.');
        } finally {
            setLoading(false);
        }
    };

    const handleExport = () => {
        const rows = newsData.map((item) => ({
            keyword: item.keyword,
            title: item.title,
            sentiment: item.sentiment_label,
            date: item.published_date,
            source: item.link,
        }));
        exportAsCsv('market_trends_news.csv', rows);
    };

    const handleSuggestionClick = (suggestion) => {
        setSearchQuery(suggestion.name);
        setShowSuggestions(false);
        runRealtimeSearch(suggestion.name);
    };

    const stats = [
        { label: 'Total News Articles', value: loading ? '...' : String(sentiment.total), trend: null, icon: Globe },
        { label: 'Positive News', value: loading ? '...' : `${sentiment.positive}%`, trend: sentiment.positive - 50, icon: Zap },
        { label: 'Negative News', value: loading ? '...' : `${sentiment.negative}%`, trend: -(sentiment.negative), icon: TrendingDown },
        { label: 'Neutral News', value: loading ? '...' : `${sentiment.neutral}%`, trend: null, status: 'Mixed', icon: TrendingUp },
    ];

    return (
        <DashboardLayout title="Market Trends Analysis">
            {/* Breadcrumbs & Header */}
            <div className="space-y-8">
                <div className="flex items-center gap-2 text-sm text-slate-500">
                    <span>Dashboard</span>
                    <ChevronRight className="w-4 h-4" />
                    <span className="text-white font-bold">Market Trends Analysis</span>
                </div>

                <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
                    <div className="max-w-3xl">
                        <h1 className="text-4xl font-black text-white tracking-tight mb-3">Market Trends Analysis</h1>
                        <p className="text-slate-400 text-lg leading-relaxed">
                            Real-time news sentiment and keyword trend analysis across global markets.
                        </p>
                    </div>
                    <div className="flex gap-4">
                        
                        <button onClick={handleExport} className="flex items-center gap-2 px-6 py-3 bg-white/5 border border-white/10 rounded-xl text-sm font-bold hover:bg-white/10 transition-all">
                            <Download className="w-4 h-4" /> Export Data
                        </button>
                    </div>
                </div>

                {error && (
                    <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl px-4 py-3 text-sm text-rose-300">
                        {error}
                    </div>
                )}

                {/* Search Bar with Suggestions */}
                <div className="relative">
                    <div className="relative bg-white/[0.03] border border-white/10 rounded-2xl flex items-center px-4 py-3">
                        <Search className="w-5 h-5 text-slate-400 mr-3" />
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                    e.preventDefault();
                                    runRealtimeSearch();
                                }
                            }}
                            placeholder="Search keywords (e.g., iPhone, Amazon, Nike)..."
                            className="flex-1 bg-transparent outline-none text-white placeholder:text-slate-500 text-sm"
                        />
                    </div>

                    {/* Suggestions Dropdown */}
                    {showSuggestions && filteredSuggestions.length > 0 && (
                        <motion.div
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="absolute top-full left-0 right-0 mt-2 bg-slate-900 border border-white/10 rounded-2xl shadow-2xl z-50 overflow-hidden"
                        >
                            <div className="max-h-64 overflow-y-auto">
                                {filteredSuggestions.map((suggestion, idx) => (
                                    <button
                                        key={idx}
                                        onClick={() => handleSuggestionClick(suggestion)}
                                        className="w-full px-4 py-3 text-left hover:bg-white/5 border-b border-white/5 last:border-b-0 transition-colors flex items-center justify-between group"
                                    >
                                        <div>
                                            <p className="text-white font-medium text-sm">{suggestion.name}</p>
                                            <p className="text-xs text-slate-500">{suggestion.category}</p>
                                        </div>
                                        <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-primary" />
                                    </button>
                                ))}
                            </div>
                        </motion.div>
                    )}
                </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
                {stats.map((stat, i) => (
                    <motion.div
                        key={stat.label}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.1 }}
                        className="bg-white/[0.03] border border-white/10 p-8 rounded-[2.5rem] relative group hover:border-white/20 transition-all"
                    >
                        <div className="absolute top-0 right-0 w-24 h-24 bg-primary/5 blur-3xl rounded-full translate-x-12 -translate-y-12"></div>
                        <div className="flex items-center justify-between mb-6">
                            <p className="text-xs font-black uppercase text-slate-500 tracking-widest">{stat.label}</p>
                            <stat.icon className="w-5 h-5 text-primary opacity-50 group-hover:opacity-100 transition-opacity" />
                        </div>
                        <div className="flex items-end gap-3 relative z-10">
                            <h3 className="text-3xl font-black">{stat.value}</h3>
                            {stat.trend != null && (
                                <span className={`text-sm font-bold flex items-center mb-1 ${stat.trend > 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                                    {stat.trend > 0 ? <TrendingUp className="w-4 h-4 mr-1" /> : <TrendingDown className="w-4 h-4 mr-1" />}
                                    {Math.abs(stat.trend)}%
                                </span>
                            )}
                            {stat.status && (
                                <span className="px-2 py-0.5 rounded bg-primary text-background-dark text-[10px] font-black uppercase mb-1">{stat.status}</span>
                            )}
                        </div>
                    </motion.div>
                ))}
            </div>

            {/* Sentiment Analysis & Trending Keywords */}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
                {/* News Sentiment Summary */}
                <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    className="bg-white/[0.03] border border-white/10 p-10 rounded-[3rem] shadow-2xl hover:border-white/20 transition-all"
                >
                    <h4 className="text-2xl font-bold mb-2">News Sentiment Summary</h4>
                    <p className="text-sm text-slate-500 mb-6">Sentiment breakdown across {sentiment.total} articles</p>
                    {loading ? (
                        <div className="flex items-center justify-center h-32">
                            <Loader2 className="w-12 h-12 text-primary animate-spin" />
                        </div>
                    ) : (
                        <div className="space-y-6">
                            {/* Sentiment Progress Bars */}
                            <div className="space-y-4">
                                {/* Positive */}
                                <div>
                                    <div className="flex justify-between items-center mb-2">
                                        <span className="text-sm font-semibold text-slate-300">Positive Sentiment</span>
                                        <span className="text-lg font-black text-emerald-400">{sentiment.positive}%</span>
                                    </div>
                                    <div className="h-2.5 bg-white/5 rounded-full overflow-hidden border border-white/10">
                                        <motion.div
                                            initial={{ width: 0 }}
                                            whileInView={{ width: `${sentiment.positive}%` }}
                                            transition={{ duration: 1 }}
                                            className="h-full bg-emerald-400 rounded-full"
                                        />
                                    </div>
                                </div>

                                {/* Neutral */}
                                <div>
                                    <div className="flex justify-between items-center mb-2">
                                        <span className="text-sm font-semibold text-slate-300">Neutral Sentiment</span>
                                        <span className="text-lg font-black text-slate-400">{sentiment.neutral}%</span>
                                    </div>
                                    <div className="h-2.5 bg-white/5 rounded-full overflow-hidden border border-white/10">
                                        <motion.div
                                            initial={{ width: 0 }}
                                            whileInView={{ width: `${sentiment.neutral}%` }}
                                            transition={{ duration: 1, delay: 0.2 }}
                                            className="h-full bg-slate-400 rounded-full"
                                        />
                                    </div>
                                </div>

                                {/* Negative */}
                                <div>
                                    <div className="flex justify-between items-center mb-2">
                                        <span className="text-sm font-semibold text-slate-300">Negative Sentiment</span>
                                        <span className="text-lg font-black text-rose-400">{sentiment.negative}%</span>
                                    </div>
                                    <div className="h-2.5 bg-white/5 rounded-full overflow-hidden border border-white/10">
                                        <motion.div
                                            initial={{ width: 0 }}
                                            whileInView={{ width: `${sentiment.negative}%` }}
                                            transition={{ duration: 1, delay: 0.4 }}
                                            className="h-full bg-rose-400 rounded-full"
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* Recent Headlines */}
                            <div className="border-t border-white/10 pt-6">
                                <h5 className="text-sm font-black text-slate-400 uppercase tracking-widest mb-4">Recent Headlines</h5>
                                <div className="space-y-3 text-sm max-h-48 overflow-y-auto">
                                    {newsData.slice(0, 4).map((n, i) => (
                                        <motion.div
                                            key={i}
                                            initial={{ opacity: 0, x: -10 }}
                                            whileInView={{ opacity: 1, x: 0 }}
                                            transition={{ delay: i * 0.1 }}
                                            className="flex items-start gap-3 p-3 bg-white/[0.02] rounded-lg hover:bg-white/5 transition-colors border border-white/5"
                                        >
                                            <span className={`text-2xl ${n.sentiment_label === 'Positive' ? 'text-emerald-400' : n.sentiment_label === 'Negative' ? 'text-rose-400' : 'text-slate-400'}`}>•</span>
                                            <div className="flex-1 min-w-0">
                                                <p className="text-slate-300 line-clamp-2">{n.title || 'News Article'}</p>
                                                <div className="flex items-center gap-2 mt-1">
                                                    <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                                                        n.sentiment_label === 'Positive' ? 'bg-emerald-500/20 text-emerald-300' :
                                                        n.sentiment_label === 'Negative' ? 'bg-rose-500/20 text-rose-300' :
                                                        'bg-slate-500/20 text-slate-300'
                                                    }`}>
                                                        {n.sentiment_label}
                                                    </span>
                                                    <span className="text-xs text-slate-600">{n.source || 'News'}</span>
                                                </div>
                                            </div>
                                        </motion.div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}
                </motion.div>

                {/* Trending Keywords */}
                <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    className="bg-white/[0.03] border border-white/10 p-10 rounded-[3rem] shadow-2xl hover:border-white/20 transition-all"
                >
                    <h4 className="text-2xl font-bold mb-2">Trending Keywords</h4>
                    <p className="text-sm text-slate-500 mb-6">Top keywords mentioned in news</p>
                    {loading ? (
                        <div className="flex items-center justify-center h-32">
                            <Loader2 className="w-12 h-12 text-primary animate-spin" />
                        </div>
                    ) : keywords.length > 0 ? (
                        <div className="space-y-3">
                            {keywords.map((keyword, i) => (
                                <motion.div
                                    key={keyword.rank}
                                    initial={{ opacity: 0, y: 10 }}
                                    whileInView={{ opacity: 1, y: 0 }}
                                    transition={{ delay: i * 0.08 }}
                                    className="group"
                                >
                                    <div className="flex items-center gap-4 p-4 bg-white/[0.02] rounded-xl hover:bg-white/5 border border-white/5 hover:border-primary/30 transition-all cursor-pointer">
                                        <div className="text-lg font-black text-primary bg-gradient-to-br from-primary/20 to-primary/10 border border-primary/30 rounded-lg px-3 py-2 min-w-14 text-center">
                                            #{keyword.rank}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="font-bold text-white text-sm">{keyword.name}</p>
                                            <p className="text-xs text-slate-500">{keyword.growth} articles mentioned</p>
                                        </div>
                                        <TrendingUp className="w-4 h-4 text-emerald-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                                    </div>
                                    {/* Progress bar under keyword */}
                                    <div className="h-1.5 bg-white/5 rounded-full overflow-hidden mt-2 border border-white/5">
                                        <motion.div
                                            initial={{ width: 0 }}
                                            whileInView={{ width: `${keyword.val}%` }}
                                            transition={{ duration: 1.5, delay: i * 0.1 }}
                                            className="h-full bg-gradient-to-r from-primary to-emerald-400"
                                        />
                                    </div>
                                </motion.div>
                            ))}
                        </div>
                    ) : (
                        <p className="text-slate-400 text-sm text-center py-8">No trending keywords available.</p>
                    )}
                </motion.div>
            </div>

            {insights.length > 0 && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="bg-white/[0.03] border border-white/10 p-8 rounded-[2.5rem]"
                >
                    <h4 className="text-2xl font-bold mb-4">AI Insights</h4>
                    <div className="space-y-3">
                        {insights.map((insight, idx) => (
                            <div key={`${idx}-${insight}`} className="p-3 rounded-xl bg-white/[0.02] border border-white/10 text-slate-200 text-sm">
                                {insight}
                            </div>
                        ))}
                    </div>
                </motion.div>
            )}
        </DashboardLayout>
    );
};

export default MarketTrends;
