import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
    Download, Calendar, MessageSquare, Smile, Frown, Meh,
    Zap, Search, TrendingUp, TrendingDown, Loader2, RefreshCcw,
    AlertCircle, ChevronRight, ExternalLink, BarChart3
} from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';
import { apiFetch, apiFetchJSON, exportAsCsv } from '../lib/api';
import { sentimentBreakdown } from '../lib/sentiment';

const SENTIMENT_COLORS = {
    Positive: { text: 'text-emerald-400', bg: 'bg-emerald-400/10', border: 'border-emerald-400/30', dot: 'bg-emerald-400' },
    Neutral:  { text: 'text-slate-400',   bg: 'bg-slate-400/10',   border: 'border-slate-400/30',   dot: 'bg-slate-400'   },
    Negative: { text: 'text-rose-400',    bg: 'bg-rose-400/10',    border: 'border-rose-400/30',    dot: 'bg-rose-400'    },
};

const Sentiment = () => {
    const navigate = useNavigate();
    const [sentimentData, setSentimentData] = useState({ positive: 0, neutral: 0, negative: 0, total: 0 });
    const [loading, setLoading]     = useState(true);
    const [avgScore, setAvgScore]   = useState(0);
    const [query, setQuery]         = useState('iphone');
    const [liveData, setLiveData]   = useState(null);
    const [liveLoading, setLiveLoading] = useState(false);
    const [liveError, setLiveError] = useState('');
    const initializedRef = useRef(false);

    // ── Auth guard + initial data load ────────────────────────────────────────
    useEffect(() => {
        if (initializedRef.current) return;
        initializedRef.current = true;

        const token = localStorage.getItem('token');
        if (!token) {
            navigate('/login');
            return;
        }
        fetchData();
        // Auto-run the live scan immediately with the default query
        runRealtimeAnalysis(false);     // false = allow cache hit for speed
    }, []);

    // ── Aggregate data from MongoDB via /api/products ─────────────────────────
    const fetchData = async () => {
        try {
            setLoading(true);
            const result = await apiFetchJSON('/api/products');
            const data   = result.data || [];

            const breakdown = sentimentBreakdown(data);
            const { Positive: pos, Negative: neg, Neutral: neu, total } = breakdown;

            setSentimentData({
                positive: total > 0 ? Math.round((pos / total) * 100) : 0,
                neutral:  total > 0 ? Math.round((neu / total) * 100) : 0,
                negative: total > 0 ? Math.round((neg / total) * 100) : 0,
                total,
            });

            const score = total > 0 ? Math.round((pos * 100 + neu * 50) / total) : 0;
            setAvgScore(score);
        } catch (error) {
            console.error('fetchData error:', error);
        } finally {
            setLoading(false);
        }
    };

    // ── Live Scan via /api/realtime/analyze ───────────────────────────────────
    const runRealtimeAnalysis = async (forceRefresh = true) => {
        if (!query.trim()) return;

        try {
            setLiveLoading(true);
            setLiveError('');
            const result = await apiFetchJSON('/api/realtime/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    product:       query.trim(),
                    max_articles:  30,
                    force_refresh: forceRefresh,
                }),
            });
            setLiveData(result);
        } catch (error) {
            console.error('Live scan error:', error);
            setLiveError(error.message || 'Live scan failed. Check that the backend is running.');
        } finally {
            setLiveLoading(false);
        }
    };

    // ── CSV Export ────────────────────────────────────────────────────────────
    const exportLiveReport = () => {
        if (!liveData) return;
        const rows = (liveData.top_articles || []).map((a) => ({
            product:      liveData.product,
            date:         a.published_date,
            source:       liveData.source,
            title:        a.title,
            sentiment:    a.sentiment_label,
            confidence:   a.confidence_score,
            price_signal: a.price_signal,
        }));
        exportAsCsv(`${(liveData.product || 'sentiment').replace(/\s+/g, '_')}_realtime_report.csv`, rows);
    };

    // Stats cards ─────────────────────────────────────────────────────────────
    // Prefer live scan numbers when available
    const liveSentiment = liveData?.sentiment_breakdown;
    const liveTotal     = liveData?.article_count || 0;
    const displayTotal  = liveSentiment
        ? liveTotal
        : sentimentData.total;
    const displayPos    = liveSentiment
        ? Math.round(((liveSentiment.positive || 0) / Math.max(liveTotal, 1)) * 100)
        : sentimentData.positive;

    const stats = [
        {
            label: 'Total Mentions',
            value: loading ? '…' : displayTotal,
            trend: 12.5,
            icon:  MessageSquare,
        },
        {
            label: 'Sentiment Score',
            value: loading ? '…' : liveData?.sentiment_score != null
                ? Math.round(((liveData.sentiment_score + 100) / 2))   // map -100..100 → 0..100
                : avgScore,
            outOf: '/100',
            trend: displayPos - sentimentData.negative,
            icon:  BarChart3,
        },
        {
            label: 'Positive Rate',
            value: loading ? '…' : `${displayPos}%`,
            trend: displayPos - 50,
            icon:  Smile,
        },
    ];

    return (
        <DashboardLayout title="Sentiment Analysis">

            {/* ── Header ─────────────────────────────────────────────────────── */}
            <div className="flex flex-wrap items-center justify-between gap-8">
                <div className="space-y-2">
                    <h1 className="text-4xl font-black text-white tracking-tight">Sentiment Analysis</h1>
                    <div className="flex items-center gap-3 text-slate-400">
                        <Zap className="w-5 h-5 text-primary" />
                        <p className="text-lg">
                            {loading ? 'Loading…' : sentimentData.total > 0
                                ? `Analysing ${sentimentData.total} stored reviews`
                                : 'All Products'}
                        </p>
                    </div>
                </div>
                <div className="flex gap-4">
                    <button
                        onClick={() => runRealtimeAnalysis(true)}
                        disabled={liveLoading}
                        className="flex items-center gap-3 px-6 py-3 bg-white/5 border border-white/10 rounded-2xl text-sm font-bold hover:bg-white/10 transition-all disabled:opacity-50"
                    >
                        <Calendar className="w-5 h-5 text-primary" /> Last 30 Days
                    </button>
                    <button
                        onClick={exportLiveReport}
                        className="flex items-center gap-3 px-6 py-3 bg-primary text-background-dark rounded-2xl text-sm font-black shadow-lg shadow-primary/20"
                    >
                        <Download className="w-5 h-5" /> Export Report
                    </button>
                </div>
            </div>

            {/* ── Live Scan bar ───────────────────────────────────────────────── */}
            <div className="bg-white/[0.03] border border-white/10 p-6 rounded-3xl flex flex-col lg:flex-row gap-4 lg:items-center lg:justify-between">
                <div className="flex items-center gap-3 flex-1">
                    <Search className="w-5 h-5 text-slate-400 shrink-0" />
                    <input
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && runRealtimeAnalysis(true)}
                        placeholder="Product name for real-time analysis (e.g., iPhone 16, Nike shoes)"
                        className="w-full bg-transparent outline-none text-slate-200 placeholder:text-slate-600"
                    />
                </div>
                <div className="flex items-center gap-3">
                    <button
                        onClick={() => runRealtimeAnalysis(true)}
                        disabled={liveLoading || !query.trim()}
                        className="px-6 py-2.5 rounded-xl bg-primary text-background-dark font-bold text-sm disabled:opacity-50 flex items-center gap-2 shadow-lg shadow-primary/20"
                    >
                        {liveLoading
                            ? <><Loader2 className="w-4 h-4 animate-spin" /> Scanning…</>
                            : <><RefreshCcw className="w-4 h-4" /> Live Scan</>}
                    </button>
                    {liveData?.budget && (
                        <span className="text-xs text-slate-400 hidden sm:block">
                            API budget: <strong className="text-primary">{liveData.budget.remaining}</strong>/{liveData.budget.limit} left
                        </span>
                    )}
                </div>
            </div>

            {/* ── Error Banner ────────────────────────────────────────────────── */}
            {liveError && (
                <motion.div
                    initial={{ opacity: 0, y: -6 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex items-start gap-3 text-sm text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-2xl px-5 py-4"
                >
                    <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                    {liveError}
                </motion.div>
            )}

            {/* ── Stats Grid ─────────────────────────────────────────────────── */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {stats.map((stat, i) => (
                    <motion.div
                        key={stat.label}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.1 }}
                        className="bg-white/[0.03] border border-white/10 p-10 rounded-[3rem] shadow-2xl relative group overflow-hidden"
                    >
                        <div className={`absolute top-0 right-0 w-32 h-32 blur-3xl rounded-full opacity-10 transition-opacity group-hover:opacity-20 ${stat.trend > 0 ? 'bg-emerald-500' : 'bg-rose-500'}`} />
                        <div className="flex items-center justify-between mb-8 relative z-10">
                            <p className="text-xs font-black uppercase text-slate-500 tracking-widest">{stat.label}</p>
                            <stat.icon className="w-6 h-6 text-primary" />
                        </div>
                        <div className="relative z-10">
                            <h3 className="text-4xl font-black mb-3">
                                {stat.value}
                                {stat.outOf && <span className="text-xl text-slate-600 ml-1">{stat.outOf}</span>}
                            </h3>
                            <div className={`flex items-center gap-2 text-sm font-bold ${stat.trend > 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                                {stat.trend > 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                                <span>{stat.trend > 0 ? '+' : ''}{typeof stat.trend === 'number' ? stat.trend.toFixed(1) : stat.trend}%</span>
                            </div>
                        </div>
                    </motion.div>
                ))}
            </div>

            {/* ── Breakdown + Trend ───────────────────────────────────────────── */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">

                {/* Sentiment Breakdown bars */}
                <motion.div
                    initial={{ opacity: 0, x: -30 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    className="bg-white/[0.03] border border-white/10 p-12 rounded-[3.5rem] shadow-2xl"
                >
                    <h2 className="text-2xl font-bold mb-2">Sentiment Breakdown</h2>
                    <p className="text-sm text-slate-500 mb-10">
                        {liveData ? `Live: "${liveData.product}" — ${liveData.article_count} mentions` : 'Stored reviews'}
                    </p>
                    {loading ? (
                        <div className="flex items-center justify-center h-48">
                            <Loader2 className="w-12 h-12 text-primary animate-spin" />
                        </div>
                    ) : (
                        <div className="space-y-10">
                            {[
                                { label: 'Positive', val: liveSentiment ? liveSentiment.positive : sentimentData.positive, raw: !liveSentiment, color: 'bg-emerald-400', icon: Smile },
                                { label: 'Neutral',  val: liveSentiment ? liveSentiment.neutral  : sentimentData.neutral,  raw: !liveSentiment, color: 'bg-slate-400',   icon: Meh   },
                                { label: 'Negative', val: liveSentiment ? liveSentiment.negative : sentimentData.negative, raw: !liveSentiment, color: 'bg-rose-400',    icon: Frown },
                            ].map((item) => {
                                const pct = item.raw
                                    ? item.val           // already a percentage from stored data
                                    : Math.round((item.val / Math.max(liveTotal, 1)) * 100);
                                return (
                                    <div key={item.label} className="space-y-4">
                                        <div className="flex justify-between items-center">
                                            <div className="flex items-center gap-3">
                                                <item.icon className={`w-5 h-5 ${item.color.replace('bg', 'text')}`} />
                                                <span className="text-sm font-bold text-slate-300">{item.label}</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                {!item.raw && <span className="text-xs text-slate-500">{item.val} mentions</span>}
                                                <span className="text-xl font-black text-white">{pct}%</span>
                                            </div>
                                        </div>
                                        <div className="h-4 w-full bg-white/5 rounded-full overflow-hidden p-[2px] border border-white/5">
                                            <motion.div
                                                initial={{ width: 0 }}
                                                whileInView={{ width: `${pct}%` }}
                                                transition={{ duration: 1.5 }}
                                                className={`${item.color} h-full rounded-full`}
                                            />
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </motion.div>

                {/* Sentiment Summary & Analysis */}
                <motion.div
                    initial={{ opacity: 0, x: 30 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    className="bg-white/[0.03] border border-white/10 p-12 rounded-[3.5rem] shadow-2xl"
                >
                    <h2 className="text-2xl font-bold mb-8">Sentiment Summary</h2>

                    {!liveData ? (
                        <div className="text-slate-400 text-center py-8">
                            <p className="mb-4">Run a Live Scan above to see sentiment analysis and market insights.</p>
                            <p className="text-sm">The analysis will include daily trends and price sensitivity data.</p>
                        </div>
                    ) : (
                        <div className="space-y-6">
                            {/* Overall Summary */}
                            <div className="bg-white/[0.02] border border-white/10 rounded-2xl p-6">
                                <h3 className="font-bold text-white mb-3">Overall Sentiment</h3>
                                <p className="text-slate-300">{liveData?.summary || 'Analyzing sentiment data...'}</p>
                            </div>

                            {/* Daily Trend Summary */}
                            {liveData?.daily_trend && liveData.daily_trend.length > 0 && (
                                <div className="bg-white/[0.02] border border-white/10 rounded-2xl p-6">
                                    <h3 className="font-bold text-white mb-3">Daily Trend</h3>
                                    <div className="space-y-2 text-sm text-slate-300">
                                        {liveData.daily_trend.slice(-7).map((day, idx) => (
                                            <div key={idx} className="flex justify-between items-center">
                                                <span className="text-slate-400">{day.date}</span>
                                                <span className={`font-bold ${day.score > 0 ? 'text-emerald-400' : day.score < 0 ? 'text-rose-400' : 'text-slate-400'}`}>
                                                    {day.score > 0 ? '+' : ''}{day.score.toFixed(2)} ({day.samples} samples)
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Price Sensitivity */}
                            {liveData?.price_sensitivity && (
                                <div className="bg-white/[0.02] border border-white/10 rounded-2xl p-6">
                                    <h3 className="font-bold text-white mb-3">Price Sensitivity</h3>
                                    <div className="space-y-2 text-sm">
                                        <div className="flex justify-between">
                                            <span className="text-slate-400">Positive price mentions:</span>
                                            <span className="text-emerald-400 font-bold">{liveData.price_sensitivity.price_positive_mentions}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-slate-400">Negative price mentions:</span>
                                            <span className="text-rose-400 font-bold">{liveData.price_sensitivity.price_negative_mentions}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-slate-400">Sensitivity Index:</span>
                                            <span className="text-primary font-bold">{liveData.price_sensitivity.price_sensitivity_index?.toFixed(2)}</span>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </motion.div>
            </div>

            {/* ── Insights & Yearly Trend ─────────────────────────────────────── */}
            {liveData?.insights?.length > 0 && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-white/[0.03] border border-white/10 rounded-3xl p-8"
                >
                    <h3 className="text-xl font-bold mb-5">Key Insights — {liveData.product}</h3>
                    <ul className="space-y-3">
                        {liveData.insights.map((insight, i) => (
                            <li key={i} className="flex items-start gap-3 text-slate-300 text-sm">
                                <ChevronRight className="w-4 h-4 text-primary mt-0.5 shrink-0" />
                                {insight}
                            </li>
                        ))}
                    </ul>
                </motion.div>
            )}

            {/* ── Article Cards ──────────────────────────────────────────────── */}
            {liveData?.top_articles?.length > 0 && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="space-y-4"
                >
                    <div className="flex items-center justify-between">
                        <h3 className="text-xl font-bold">
                            Recent Mentions
                            <span className="ml-3 text-sm font-normal text-slate-500">
                                {liveData.article_count} total · showing {liveData.top_articles.length}
                            </span>
                        </h3>
                        <button onClick={exportLiveReport} className="text-xs text-primary font-bold hover:underline flex items-center gap-1">
                            <Download className="w-3.5 h-3.5" /> Export CSV
                        </button>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {liveData.top_articles.map((article, i) => {
                            const sentKey   = article.sentiment_label || 'Neutral';
                            const colors    = SENTIMENT_COLORS[sentKey] || SENTIMENT_COLORS.Neutral;
                            const scoreText = article.confidence_score != null
                                ? `${Math.round(article.confidence_score * 100)}% confidence`
                                : '';
                            return (
                                <motion.div
                                    key={i}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: i * 0.04 }}
                                    className="bg-white/[0.03] border border-white/10 rounded-2xl p-5 hover:border-primary/30 transition-all"
                                >
                                    <div className="flex items-start justify-between gap-3 mb-3">
                                        <p className="text-sm font-medium text-slate-200 line-clamp-2 leading-snug flex-1">
                                            {article.title || article.description?.slice(0, 100) || 'No title'}
                                        </p>
                                        <span className={`text-xs font-bold px-2.5 py-1 rounded-full border whitespace-nowrap ${colors.text} ${colors.bg} ${colors.border}`}>
                                            <span className={`inline-block w-1.5 h-1.5 rounded-full ${colors.dot} mr-1.5`} />
                                            {sentKey}
                                        </span>
                                    </div>
                                    <div className="flex items-center justify-between text-xs text-slate-500">
                                        <span>{article.published_date?.slice(0, 10) || 'Unknown date'}</span>
                                        <div className="flex items-center gap-3">
                                            {scoreText && <span className="text-slate-600">{scoreText}</span>}
                                            {article.link && (
                                                <a href={article.link} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline flex items-center gap-1">
                                                    Source <ExternalLink className="w-3 h-3" />
                                                </a>
                                            )}
                                        </div>
                                    </div>
                                </motion.div>
                            );
                        })}
                    </div>
                </motion.div>
            )}

        </DashboardLayout>
    );
};

export default Sentiment;
