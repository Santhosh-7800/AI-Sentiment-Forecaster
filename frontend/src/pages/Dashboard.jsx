import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from "react-router-dom";
import { motion } from 'framer-motion';
import {
    Search, Sparkles, TrendingUp, Globe2, ArrowUpRight, Zap, Loader2,
    RefreshCcw, BarChart3, MessageSquare, AlertCircle, ChevronRight
} from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';
import { apiFetchJSON } from '../lib/api';
import { sentimentBreakdown } from '../lib/sentiment';
import PipelineStatus from '../components/PipelineStatus';

const Dashboard = () => {
    const navigate = useNavigate();

    // Stored aggregate data
    const [sentimentData, setSentimentData] = useState({ positive: 0, neutral: 0, negative: 0, total: 0 });
    const [systemStats, setSystemStats]     = useState(null);
    const [topProducts, setTopProducts]     = useState([]);
    const [loading, setLoading]             = useState(true);
    const [categories, setCategories]       = useState([]);

    // Live scan
    const [searchQuery, setSearchQuery]       = useState('');
    const [analysisReport, setAnalysisReport] = useState(null);
    const [analysisError, setAnalysisError]   = useState('');
    const [ragLoading, setRagLoading]         = useState(false);

    // Product insights (Groq)
    const [insights, setInsights]             = useState(null);
    const [insightsLoading, setInsightsLoading] = useState(false);
    const [insightsError, setInsightsError]   = useState('');

    const initializedRef = useRef(false);

    // ── Auth guard + initial data ──────────────────────────────────────────────
    useEffect(() => {
        if (initializedRef.current) return;
        initializedRef.current = true;
        const token = localStorage.getItem("token");
        if (!token) { navigate("/login"); return; }
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);

            // Fetch both in parallel
            const [productsResult, statsResult] = await Promise.allSettled([
                apiFetchJSON('/api/products'),
                apiFetchJSON('/api/stats'),
            ]);

            if (productsResult.status === 'fulfilled') {
                const data = productsResult.value.data || [];
                const breakdown = sentimentBreakdown(data);
                const { Positive: pos, Negative: neg, Neutral: neu, total } = breakdown;
                setSentimentData({
                    positive: total > 0 ? Math.round((pos / total) * 100) : 0,
                    neutral:  total > 0 ? Math.round((neu / total) * 100) : 0,
                    negative: total > 0 ? Math.round((neg / total) * 100) : 0,
                    total,
                });
                const uniqueCategories = [...new Set(data.map(i => i.category).filter(Boolean))];
                setCategories(uniqueCategories);

                // Build top products by category
                const byCategory = {};
                for (const item of data) {
                    const cat = item.category || 'Other';
                    if (!byCategory[cat]) byCategory[cat] = [];
                    byCategory[cat].push(item);
                }
                const products = Object.entries(byCategory).map(([cat, items]) => {
                    const posCount = items.filter(i => (i.sentiment_label || '').toLowerCase().startsWith('pos')).length;
                    return {
                        name:     cat,
                        total:    items.length,
                        positive: posCount,
                        pct:      items.length ? Math.round((posCount / items.length) * 100) : 0,
                    };
                }).sort((a, b) => b.pct - a.pct).slice(0, 6);
                setTopProducts(products);
            }

            if (statsResult.status === 'fulfilled') {
                setSystemStats(statsResult.value);
            }
        } catch (error) {
            console.error('Dashboard fetchData error:', error);
        } finally {
            setLoading(false);
        }
    };

    // ── Live Scan ─────────────────────────────────────────────────────────────
    const handleSearch = async () => {
        if (!searchQuery.trim()) return;
        try {
            setRagLoading(true);
            setAnalysisError('');
            setInsights(null);
            setInsightsError('');

            const result = await apiFetchJSON('/api/realtime/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    product:       searchQuery.trim(),
                    max_articles:  40,
                    force_refresh: true,
                }),
            });
            setAnalysisReport(result);

            // Fetch AI insights after analysis completes
            await fetchProductInsights(searchQuery.trim(), result.sentiment_breakdown);
        } catch (error) {
            console.error('Live scan error:', error);
            setAnalysisError(error.message || 'Analysis failed.');
            setAnalysisReport(null);
        } finally {
            setRagLoading(false);
        }
    };

    // ── Fetch Product Insights from Groq ───────────────────────────────────────
    const fetchProductInsights = async (productName, sentimentBreakdown) => {
        try {
            setInsightsLoading(true);
            setInsights(null);
            setInsightsError('');

            const result = await apiFetchJSON('/api/product-insights/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    product: productName,
                    sentiment_breakdown: {
                        positive: sentimentBreakdown?.positive || 0,
                        neutral: sentimentBreakdown?.neutral || 0,
                        negative: sentimentBreakdown?.negative || 0,
                    },
                }),
            });

            setInsights(result);
        } catch (error) {
            console.error('Insights fetch error:', error);
            setInsightsError(error.message || 'Failed to generate insights');
        } finally {
            setInsightsLoading(false);
        }
    };

    // Quick overview tiles
    const overviewStats = [
        { label: 'Total Reviews',      value: loading ? '…' : (systemStats?.total_reviews  ?? sentimentData.total),                  icon: MessageSquare, color: 'text-primary'     },
        { label: 'Positive Sentiment', value: loading ? '…' : `${systemStats?.positive_pct ?? sentimentData.positive}%`,              icon: TrendingUp,    color: 'text-emerald-400' },
        { label: 'Negative Sentiment', value: loading ? '…' : `${systemStats?.negative_pct ?? sentimentData.negative}%`,              icon: AlertCircle,   color: 'text-rose-400'    },
        { label: 'Categories',         value: loading ? '…' : categories.length,                                                      icon: BarChart3,     color: 'text-violet-400'  },
    ];

    return (
        <DashboardLayout title="Insights Dashboard">
            <div className="space-y-8">
                {/* Pipeline Status */}
                <PipelineStatus />

                {/* Page header */}
                <div>
                    <h1 className="text-4xl font-black text-white tracking-tight">Market Intelligence</h1>
                    <p className="text-slate-400 mt-2 text-lg">Real-time sentiment and trend analysis for your products.</p>
                </div>

                {/* Overview stat tiles */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    {overviewStats.map((s, i) => (
                        <motion.div
                            key={s.label}
                            initial={{ opacity: 0, y: 16 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.08 }}
                            className="bg-white/[0.03] border border-white/10 rounded-3xl p-6 flex items-center gap-4"
                        >
                            <div className="p-3 bg-white/5 rounded-2xl">
                                <s.icon className={`w-6 h-6 ${s.color}`} />
                            </div>
                            <div>
                                <p className="text-2xl font-black text-white">{s.value}</p>
                                <p className="text-xs text-slate-500 font-semibold mt-0.5">{s.label}</p>
                            </div>
                        </motion.div>
                    ))}
                </div>

                {/* Trending Products Banner */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-gradient-to-r from-purple-600/20 to-blue-600/20 border border-primary/30 rounded-3xl p-8 flex items-center justify-between"
                >
                    <div className="space-y-2">
                        <div className="flex items-center gap-2">
                            <TrendingUp className="w-6 h-6 text-primary" />
                            <h3 className="text-2xl font-bold text-white">Auto-Updated Trending Products</h3>
                        </div>
                        <p className="text-slate-300">
                            View products being tracked automatically. New data added every 6 hours with sentiment analysis.
                        </p>
                    </div>
                    <button
                        onClick={() => navigate('/trending-products')}
                        className="px-8 py-3 bg-primary text-background-dark font-bold rounded-2xl hover:brightness-110 active:scale-95 transition-all whitespace-nowrap flex items-center gap-2"
                    >
                        View Trending <ArrowUpRight className="w-5 h-5" />
                    </button>
                </motion.div>

                {/* Live Scan search bar */}
                <div className="relative group">
                    <div className="absolute inset-y-0 left-0 pl-6 flex items-center pointer-events-none">
                        <Search className="w-6 h-6 text-slate-500 group-focus-within:text-primary transition-colors" />
                    </div>
                    <input
                        type="text"
                        placeholder="Enter a product name to run a live scan (e.g. iPhone 16, Nike Air Max)…"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                        className="w-full h-20 bg-white/[0.03] border border-white/10 rounded-[2rem] pl-16 pr-48 outline-none focus:border-primary/50 focus:bg-white/[0.05] transition-all text-lg shadow-2xl"
                    />
                    <button
                        onClick={handleSearch}
                        disabled={ragLoading || !searchQuery.trim()}
                        className="absolute right-3 top-3 bottom-3 px-8 bg-primary text-background-dark font-black rounded-2xl hover:brightness-110 active:scale-95 transition-all shadow-xl shadow-primary/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                        {ragLoading
                            ? <><Loader2 className="w-5 h-5 animate-spin" /> Scanning…</>
                            : <><RefreshCcw className="w-5 h-5" /> Live Scan</>}
                    </button>
                </div>

                {/* Live Scan result banner */}
                {analysisReport && (
                    <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="p-8 rounded-3xl border bg-primary/5 border-primary/20"
                    >
                        <div className="flex items-start gap-4">
                            <Sparkles className="w-6 h-6 text-primary mt-1 shrink-0" />
                            <div className="flex-1">
                                <div className="flex items-center justify-between flex-wrap gap-2 mb-2">
                                    <h4 className="font-bold text-lg">Live Analysis — {analysisReport.product}</h4>
                                    <div className="flex gap-4 text-sm font-semibold">
                                        <span className="text-emerald-400">+{analysisReport.sentiment_breakdown?.positive} positive</span>
                                        <span className="text-slate-400">{analysisReport.sentiment_breakdown?.neutral} neutral</span>
                                        <span className="text-rose-400">{analysisReport.sentiment_breakdown?.negative} negative</span>
                                    </div>
                                </div>
                                <p className="text-slate-300 leading-relaxed">{analysisReport.summary}</p>
                                <p className="text-sm text-slate-500 mt-3">
                                    {analysisReport.article_count} mentions · Source: {analysisReport.source}
                                    {analysisReport.cached && <span className="ml-2 text-xs bg-white/5 px-2 py-0.5 rounded-full">cached</span>}
                                </p>
                            </div>
                        </div>
                    </motion.div>
                )}

                {analysisError && (
                    <div className="flex items-center gap-3 p-4 rounded-2xl border border-rose-500/30 bg-rose-500/10 text-rose-300 text-sm">
                        <AlertCircle className="w-4 h-4 shrink-0" />
                        {analysisError}
                    </div>
                )}
            </div>

            {/* Main analytics grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Overall Sentiment Text Summary */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="lg:col-span-2 bg-white/[0.03] border border-white/10 p-10 rounded-[3rem] shadow-2xl relative overflow-hidden"
                >
                    <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 blur-[100px] rounded-full -mr-32 -mt-32" />
                    <div className="relative z-10">
                        <h3 className="text-2xl font-bold mb-8">Sentiment Summary</h3>

                        {loading ? (
                            <div className="flex items-center justify-center h-48">
                                <Loader2 className="w-12 h-12 text-primary animate-spin" />
                            </div>
                        ) : (
                            <div className="space-y-8">
                                {/* Overall Sentiment Stats */}
                                <div className="space-y-4">
                                    <h4 className="font-bold text-slate-300">Overall Sentiment Breakdown</h4>
                                    <div className="grid grid-cols-3 gap-4">
                                        <div className="bg-white/[0.02] border border-white/10 rounded-2xl p-4">
                                            <p className="text-3xl font-black text-emerald-400">{sentimentData.positive}%</p>
                                            <p className="text-xs text-slate-500 mt-1 uppercase tracking-wider">Positive</p>
                                        </div>
                                        <div className="bg-white/[0.02] border border-white/10 rounded-2xl p-4">
                                            <p className="text-3xl font-black text-slate-400">{sentimentData.neutral}%</p>
                                            <p className="text-xs text-slate-500 mt-1 uppercase tracking-wider">Neutral</p>
                                        </div>
                                        <div className="bg-white/[0.02] border border-white/10 rounded-2xl p-4">
                                            <p className="text-3xl font-black text-rose-400">{sentimentData.negative}%</p>
                                            <p className="text-xs text-slate-500 mt-1 uppercase tracking-wider">Negative</p>
                                        </div>
                                    </div>
                                </div>

                                {/* Data Summary */}
                                <div className="bg-white/[0.02] border border-white/10 rounded-2xl p-4">
                                    <p className="text-slate-300">
                                        <span className="font-bold text-white">{sentimentData.total} total reviews</span> analyzed across <span className="font-bold text-white">{categories.length} categories</span>.
                                        The majority of sentiment is <span className={`font-bold ${sentimentData.positive > sentimentData.negative ? 'text-emerald-400' : 'text-rose-400'}`}>
                                            {sentimentData.positive > sentimentData.negative ? 'positive' : sentimentData.negative > sentimentData.positive ? 'negative' : 'balanced'}
                                        </span>.
                                    </p>
                                </div>
                            </div>
                        )}
                    </div>
                </motion.div>

                {/* AI Insight card */}
                <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="bg-gradient-to-br from-primary to-blue-500 rounded-[3rem] p-10 text-background-dark flex flex-col justify-between shadow-2xl relative overflow-hidden group"
                >
                    <div className="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
                    <div className="relative z-10">
                        <div className="bg-background-dark/20 w-14 h-14 rounded-2xl flex items-center justify-center mb-8 backdrop-blur-md">
                            <Sparkles className="w-8 h-8 text-background-dark" />
                        </div>
                        <h3 className="text-3xl font-black leading-none mb-6">AI Insight Summary</h3>
                        <p className="text-lg font-bold leading-relaxed opacity-90 italic">
                            {loading ? "Loading insights…"
                                : analysisReport
                                    ? analysisReport.summary
                                    : sentimentData.total > 0
                                        ? `Analysing ${sentimentData.total} reviews across ${categories.length} categories. ${sentimentData.positive}% positive sentiment.`
                                        : "No data yet. Run a Live Scan above to generate insights."}
                        </p>
                    </div>
                    <button
                        onClick={() => navigate('/reports')}
                        className="w-full bg-background-dark text-primary py-5 rounded-2xl font-black text-sm uppercase tracking-widest hover:scale-[1.02] active:scale-95 transition-all shadow-xl relative z-10 mt-8"
                    >
                        Generate Full Report
                    </button>
                </motion.div>
            </div>

            {/* Top Categories */}
            {topProducts.length > 0 && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="bg-white/[0.03] border border-white/10 rounded-[3rem] p-10 shadow-2xl"
                >
                    <div className="flex items-center justify-between mb-8">
                        <h3 className="text-2xl font-bold">Top Categories by Sentiment</h3>
                        <button onClick={() => navigate('/sentiment')} className="text-primary flex items-center gap-1 text-sm font-bold hover:underline">
                            View all <ArrowUpRight className="w-4 h-4" />
                        </button>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                        {topProducts.map((product, i) => (
                            <motion.div
                                key={product.name}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: i * 0.06 }}
                                className="bg-white/[0.03] border border-white/10 rounded-2xl p-5 hover:border-primary/30 transition-all"
                            >
                                <div className="flex items-start justify-between mb-3">
                                    <div>
                                        <p className="font-bold text-white capitalize">{product.name}</p>
                                        <p className="text-xs text-slate-500 mt-0.5">{product.total} reviews</p>
                                    </div>
                                    <span className={`text-sm font-black px-2.5 py-1 rounded-xl ${product.pct >= 60 ? 'bg-emerald-400/10 text-emerald-400' : product.pct >= 40 ? 'bg-slate-400/10 text-slate-400' : 'bg-rose-400/10 text-rose-400'}`}>
                                        {product.pct}%
                                    </span>
                                </div>
                                <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                                    <motion.div
                                        initial={{ width: 0 }}
                                        whileInView={{ width: `${product.pct}%` }}
                                        transition={{ duration: 1.2, delay: i * 0.06 }}
                                        className={`h-full rounded-full ${product.pct >= 60 ? 'bg-emerald-400' : product.pct >= 40 ? 'bg-slate-400' : 'bg-rose-400'}`}
                                    />
                                </div>
                                <p className="text-xs text-slate-500 mt-2">{product.positive} of {product.total} positive</p>
                            </motion.div>
                        ))}
                    </div>
                </motion.div>
            )}

            {/* Analysis Breakdown */}
            {analysisReport && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="bg-white/[0.03] border border-white/10 rounded-[3rem] overflow-hidden shadow-2xl"
                >
                    <div className="p-10 border-b border-white/5">
                        <h3 className="text-2xl font-bold">Analysis Breakdown</h3>
                    </div>

                    <div className="p-10 space-y-8">
                        {/* Sentiment Breakdown */}
                        <div className="space-y-4">
                            <h4 className="text-lg font-bold flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-primary" />
                                Sentiment Breakdown
                            </h4>
                            <div className="bg-white/[0.02] border border-white/10 rounded-2xl p-6 space-y-3">
                                <div className="flex justify-between items-center">
                                    <span className="text-slate-300">Positive Mentions</span>
                                    <span className="text-emerald-400 font-bold">{analysisReport.sentiment_breakdown?.positive || 0}</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-slate-300">Neutral Mentions</span>
                                    <span className="text-slate-400 font-bold">{analysisReport.sentiment_breakdown?.neutral || 0}</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-slate-300">Negative Mentions</span>
                                    <span className="text-rose-400 font-bold">{analysisReport.sentiment_breakdown?.negative || 0}</span>
                                </div>
                            </div>
                        </div>

                        {/* Key Findings */}
                        {analysisReport.insights && analysisReport.insights.length > 0 && (
                            <div className="space-y-4">
                                <h4 className="text-lg font-bold flex items-center gap-2">
                                    <span className="w-2 h-2 rounded-full bg-primary" />
                                    Key Findings
                                </h4>
                                <div className="space-y-3">
                                    {analysisReport.insights.map((point, idx) => (
                                        <div key={idx} className="flex items-start gap-3 text-slate-300 text-sm bg-white/[0.02] border border-white/10 rounded-2xl p-4">
                                            <ChevronRight className="w-4 h-4 text-primary mt-0.5 shrink-0" />
                                            {point}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* AI-Generated Insights from Groq */}
                        {insightsLoading ? (
                            <div className="space-y-4">
                                <h4 className="text-lg font-bold flex items-center gap-2">
                                    <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                                    AI-Generated Insights
                                </h4>
                                <div className="flex items-center gap-3 text-slate-400 text-sm bg-white/[0.02] border border-white/10 rounded-2xl p-6">
                                    <Loader2 className="w-5 h-5 animate-spin text-primary" />
                                    Generating AI insights...
                                </div>
                            </div>
                        ) : insights ? (
                            <div className="space-y-4">
                                <h4 className="text-lg font-bold flex items-center gap-2">
                                    <span className="w-2 h-2 rounded-full bg-primary" />
                                    AI-Generated Insights
                                </h4>

                                {/* Product Overview */}
                                {insights.product_overview && insights.product_overview.length > 0 && (
                                    <div className="space-y-2">
                                        <p className="font-bold text-slate-300 text-sm">Product Overview</p>
                                        <div className="space-y-2 bg-white/[0.02] border border-white/10 rounded-2xl p-4">
                                            {insights.product_overview.map((point, idx) => (
                                                <div key={idx} className="flex items-start gap-2 text-slate-300 text-sm">
                                                    <span className="text-primary font-bold">•</span>
                                                    {point}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Sentiment Analysis */}
                                {insights.sentiment_analysis && insights.sentiment_analysis.length > 0 && (
                                    <div className="space-y-2">
                                        <p className="font-bold text-slate-300 text-sm">Sentiment Analysis</p>
                                        <div className="space-y-2 bg-white/[0.02] border border-white/10 rounded-2xl p-4">
                                            {insights.sentiment_analysis.map((point, idx) => (
                                                <div key={idx} className="flex items-start gap-2 text-slate-300 text-sm">
                                                    <span className="text-primary font-bold">•</span>
                                                    {point}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Recommendations */}
                                {insights.recommendations && insights.recommendations.length > 0 && (
                                    <div className="space-y-2">
                                        <p className="font-bold text-slate-300 text-sm">Market Recommendations</p>
                                        <div className="space-y-2 bg-white/[0.02] border border-white/10 rounded-2xl p-4">
                                            {insights.recommendations.map((point, idx) => (
                                                <div key={idx} className="flex items-start gap-2 text-slate-300 text-sm">
                                                    <span className="text-emerald-400 font-bold">✓</span>
                                                    {point}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        ) : insightsError ? (
                            <div className="flex items-start gap-3 p-4 rounded-2xl border border-rose-500/30 bg-rose-500/10 text-rose-300 text-sm">
                                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                                <span>{insightsError}</span>
                            </div>
                        ) : null}
                    </div>
                </motion.div>
            )}

            {/* Empty state */}
            {!analysisReport && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="bg-white/[0.03] border border-white/10 rounded-[3rem] p-16 shadow-2xl text-center"
                >
                    <Search className="w-16 h-16 text-slate-700 mx-auto mb-6" />
                    <h3 className="text-2xl font-bold text-white mb-2">No Analysis Yet</h3>
                    <p className="text-slate-400 mb-8">
                        Type a product name in the search bar above and click <span className="font-bold text-primary">Live Scan</span> to generate a detailed analysis with AI-powered insights.
                    </p>
                </motion.div>
            )}
        </DashboardLayout>
    );
};

export default Dashboard;
