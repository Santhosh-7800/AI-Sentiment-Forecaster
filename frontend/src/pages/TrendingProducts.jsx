import React, { useEffect, useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { Loader2, TrendingUp, RefreshCw, AlertCircle, Plus } from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';
import { apiFetchJSON } from '../lib/api';

const TrendingProducts = () => {
    const [trendingData, setTrendingData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [lastUpdate, setLastUpdate] = useState(null);
    const [importingAll, setImportingAll] = useState(false);
    const [importingSingle, setImportingSingle] = useState('');
    const [importMessage, setImportMessage] = useState('');
    const initializedRef = useRef(false);

    useEffect(() => {
        if (initializedRef.current) return;
        initializedRef.current = true;

        const token = localStorage.getItem("token");
        if (!token) {
            window.location.href = "/login";
            return;
        }

        // Initial fetch
        fetchTrendingData();

        // Auto-refresh every 30 seconds
        const interval = setInterval(fetchTrendingData, 30000);
        return () => clearInterval(interval);
    }, []);

    const fetchTrendingData = async () => {
        try {
            setError('');
            const result = await apiFetchJSON('/api/pipeline/latest-data');

            if (result.success && result.data) {
                // Sort by positive count (descending)
                const sorted = [...result.data].sort((a, b) => b.positive_count - a.positive_count);
                setTrendingData(sorted);
                setLastUpdate(new Date().toLocaleTimeString());
                setLoading(false);
            }
        } catch (err) {
            console.error('Error fetching trending data:', err);
            // Don't show error if no data yet
            if (trendingData.length === 0) {
                setError('Waiting for trending data... Pipeline updates every 6 hours.');
            }
            setLoading(false);
        }
    };


    const handleImmediateRefresh = async () => {
        try {
            setLoading(true);
            setError('');
            await apiFetchJSON('/api/pipeline/run-now', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
            });
            await fetchTrendingData();
        } catch (err) {
            console.error('Error running immediate refresh:', err);
            setError('Immediate refresh failed. Please try again.');
            setLoading(false);
        }
    };

    const importTrendingToReports = async (mode, product) => {
        try {
            setImportMessage('');
            if (mode === 'all') setImportingAll(true);
            if (mode === 'single') setImportingSingle(product || 'pending');

            const payload = mode === 'all' ? { mode: 'all' } : { mode: 'single', product };
            const result = await apiFetchJSON('/api/reports/custom/from-trending', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            setImportMessage(`Saved to Reports: ${result?.imported_rows || 0} records imported.`);
        } catch (err) {
            console.error('Error importing trending data to reports:', err);
            setImportMessage('Unable to save to Reports right now. Please try again.');
        } finally {
            setImportingAll(false);
            setImportingSingle('');
        }
    };

    const getSentimentColor = (label) => {
        switch (label.toLowerCase()) {
            case 'positive':
                return 'text-emerald-400';
            case 'negative':
                return 'text-rose-400';
            default:
                return 'text-slate-400';
        }
    };

    const getSentimentBg = (label) => {
        switch (label.toLowerCase()) {
            case 'positive':
                return 'bg-emerald-400/10';
            case 'negative':
                return 'bg-rose-400/10';
            default:
                return 'bg-slate-400/10';
        }
    };

    const calculateSentimentPercentage = (count, total) => {
        return total > 0 ? Math.round((count / total) * 100) : 0;
    };

    return (
        <DashboardLayout title="Trending Products">
            <div className="space-y-8">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-4xl font-black text-white tracking-tight">Trending Products</h1>
                        <p className="text-slate-400 mt-2 text-lg">
                            Auto-updated products with sentiment analysis (refreshes every 6 hours)
                        </p>
                    </div>
                    <div className="flex items-center gap-3">
                        <button
                            onClick={() => importTrendingToReports('all')}
                            disabled={importingAll || loading || !trendingData.length}
                            className="flex items-center gap-2 px-5 py-3 bg-white/10 border border-white/15 text-white rounded-2xl hover:border-primary/50 transition-all disabled:opacity-50"
                        >
                            {importingAll ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                            Add All To Reports
                        </button>
                        <button
                            onClick={handleImmediateRefresh}
                            disabled={loading}
                            className="flex items-center gap-2 px-6 py-3 bg-primary text-background-dark font-bold rounded-2xl hover:brightness-110 active:scale-95 transition-all disabled:opacity-50"
                        >
                            <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
                            Refresh Now
                        </button>
                    </div>
                </div>

                {importMessage && (
                    <div className="text-sm text-primary bg-primary/10 border border-primary/20 rounded-xl px-4 py-3">
                        {importMessage}
                    </div>
                )}

                    <button
                        onClick={fetchTrendingData}
                        disabled={loading}
                        className="flex items-center gap-2 px-6 py-3 bg-primary text-background-dark font-bold rounded-2xl hover:brightness-110 active:scale-95 transition-all disabled:opacity-50"
                    >
                        <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
                        Refresh Now
                    </button>
                </div>


                {/* Last Update Time */}
                {lastUpdate && (
                    <div className="text-sm text-slate-400">
                        Last updated: <span className="text-primary font-bold">{lastUpdate}</span>
                    </div>
                )}

                {/* Error State */}
                {error && !trendingData.length && (
                    <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="flex items-center gap-3 p-4 rounded-2xl border border-blue-500/30 bg-blue-500/10 text-blue-300 text-sm"
                    >
                        <AlertCircle className="w-5 h-5 shrink-0" />
                        {error}
                    </motion.div>
                )}

                {/* Loading State */}
                {loading && !trendingData.length && (
                    <div className="flex items-center justify-center h-64">
                        <div className="text-center space-y-4">
                            <Loader2 className="w-12 h-12 text-primary animate-spin mx-auto" />
                            <p className="text-slate-400">Loading trending products...</p>
                        </div>
                    </div>
                )}

                {/* Trending Products Grid */}
                {trendingData.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {trendingData.map((product, idx) => {
                            const total = product.positive_count + product.negative_count + product.neutral_count;
                            const posPct = calculateSentimentPercentage(product.positive_count, total);
                            const negPct = calculateSentimentPercentage(product.negative_count, total);
                            const neuPct = calculateSentimentPercentage(product.neutral_count, total);

                            return (
                                <motion.div
                                    key={product.product}
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: idx * 0.05 }}
                                    className="bg-white/[0.03] border border-white/10 rounded-3xl p-6 hover:border-primary/30 transition-all space-y-4"
                                >
                                    {/* Product Name & Date */}
                                    <div>
                                        <h3 className="text-xl font-bold text-white capitalize line-clamp-2">
                                            {product.keyword || product.product}
                                        </h3>
                                        <div className="flex items-center gap-2 mt-1 text-xs">
                                            <span className="text-primary/90 font-semibold">{product.context_type || 'News'}</span>
                                            <span className="text-slate-500">•</span>
                                            <span className="text-slate-400 line-clamp-1">
                                                {product.context_brand || product.product}
                                                {product.context_region ? `, ${product.context_region}` : ''}
                                            </span>
                                        </div>
                                            {product.product}
                                        </h3>
                                        <p className="text-xs text-slate-500 mt-1">
                                            {new Date(product.date).toLocaleDateString()}
                                        </p>
                                    </div>

                                    {/* Article Count */}
                                    <div className="flex items-center gap-2 text-sm">
                                        <TrendingUp className="w-4 h-4 text-primary" />
                                        <span className="text-slate-300">
                                            <span className="font-bold text-white">{product.article_count}</span> articles analyzed
                                        </span>
                                    </div>

                                    {/* Sentiment Breakdown - Text */}
                                    <div className="space-y-2 bg-white/[0.02] border border-white/10 rounded-2xl p-4">
                                        <div className="flex items-center justify-between text-sm">
                                            <span className="text-emerald-400 font-bold">
                                                Positive: {product.positive_count}
                                            </span>
                                            <span className="text-emerald-400 text-xs">{posPct}%</span>
                                        </div>
                                        <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-emerald-400 transition-all"
                                                style={{ width: `${posPct}%` }}
                                            />
                                        </div>

                                        <div className="flex items-center justify-between text-sm mt-3">
                                            <span className="text-slate-400 font-bold">
                                                Neutral: {product.neutral_count}
                                            </span>
                                            <span className="text-slate-400 text-xs">{neuPct}%</span>
                                        </div>
                                        <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-slate-400 transition-all"
                                                style={{ width: `${neuPct}%` }}
                                            />
                                        </div>

                                        <div className="flex items-center justify-between text-sm mt-3">
                                            <span className="text-rose-400 font-bold">
                                                Negative: {product.negative_count}
                                            </span>
                                            <span className="text-rose-400 text-xs">{negPct}%</span>
                                        </div>
                                        <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-rose-400 transition-all"
                                                style={{ width: `${negPct}%` }}
                                            />
                                        </div>
                                    </div>

                                    {/* Sentiment Summary */}
                                    <div className="text-sm text-slate-300">
                                        Overall sentiment is{' '}
                                        <span className={`font-bold ${
                                            posPct > 50 ? 'text-emerald-400' : negPct > 30 ? 'text-rose-400' : 'text-slate-400'
                                        }`}>
                                            {posPct > 50 ? 'Positive' : negPct > 30 ? 'Negative' : 'Mixed'}
                                        </span>
                                    </div>

                                    {/* Last Updated */}
                                    <div className="text-xs text-slate-500 border-t border-white/10 pt-3">
                                        Updated: {new Date(product.last_updated).toLocaleTimeString()}
                                    </div>

                                    <button
                                        onClick={() => importTrendingToReports('single', product.product)}
                                        disabled={importingSingle === product.product || importingAll}
                                        className="w-full py-3 bg-white/5 border border-white/10 hover:border-primary/50 font-bold rounded-2xl text-xs uppercase tracking-[0.2em] transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                                    >
                                        {importingSingle === product.product ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                                        Add To Reports
                                    </button>
                                </motion.div>
                            );
                        })}
                    </div>
                ) : !loading && trendingData.length === 0 ? (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="bg-white/[0.03] border border-white/10 rounded-[3rem] p-16 text-center"
                    >
                        <TrendingUp className="w-16 h-16 text-slate-700 mx-auto mb-6" />
                        <h3 className="text-2xl font-bold text-white mb-2">No Trending Data Yet</h3>
                        <p className="text-slate-400 mb-6">
                            The automated pipeline fetches trending products every 6 hours.
                            <br />
                            Check back later or click "Refresh Now" to check for updates.
                        </p>
                        <button
                            onClick={fetchTrendingData}
                            className="px-6 py-3 bg-primary text-background-dark font-bold rounded-2xl hover:brightness-110"
                        >
                            Check for Updates
                        </button>
                    </motion.div>
                ) : null}

                {/* Stats Summary */}
                {trendingData.length > 0 && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="bg-white/[0.03] border border-white/10 rounded-3xl p-8 grid grid-cols-1 md:grid-cols-4 gap-6"
                    >
                        <div>
                            <p className="text-slate-500 text-sm uppercase tracking-wider mb-2">Total Products</p>
                            <p className="text-4xl font-black text-primary">{trendingData.length}</p>
                        </div>
                        <div>
                            <p className="text-slate-500 text-sm uppercase tracking-wider mb-2">Total Articles</p>
                            <p className="text-4xl font-black text-emerald-400">
                                {trendingData.reduce((sum, p) => sum + p.article_count, 0)}
                            </p>
                        </div>
                        <div>
                            <p className="text-slate-500 text-sm uppercase tracking-wider mb-2">Avg. Positive Sentiment</p>
                            <p className="text-4xl font-black text-emerald-400">
                                {Math.round(
                                    trendingData.reduce((sum, p) => {
                                        const total = p.positive_count + p.negative_count + p.neutral_count;
                                        return sum + (total > 0 ? (p.positive_count / total) * 100 : 0);
                                    }, 0) / trendingData.length
                                )}%
                            </p>
                        </div>
                        <div>
                            <p className="text-slate-500 text-sm uppercase tracking-wider mb-2">Last Update</p>
                            <p className="text-lg font-bold text-slate-300">{lastUpdate || 'Never'}</p>
                        </div>
                    </motion.div>
                )}
            </div>
        </DashboardLayout>
    );
};

export default TrendingProducts;
