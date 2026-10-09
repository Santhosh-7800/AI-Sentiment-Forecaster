import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Download, Plus, Search, Filter, FileText, PieChart, BarChart2, ExternalLink, Loader2, Upload, X } from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';
import { apiFetch, apiFetchJSON, exportAsCsv } from '../lib/api';

const Reports = () => {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [reports, setReports] = useState([]);
    const [stats, setStats] = useState({ total: 0, news: 0 });
    const [searchQuery, setSearchQuery] = useState('');
    const [activeTab, setActiveTab] = useState('All');
    const [rawData, setRawData] = useState({ products: [], news: [] });
    const [customReports, setCustomReports] = useState([]);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [creating, setCreating] = useState(false);

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token) { navigate('/login'); return; }
        fetchReports(token);
    }, []);

    const fetchReports = async (token) => {
        try {
            setLoading(true);
            const [prodRes, newsRes, customRes] = await Promise.all([
                fetch('/api/products', { headers: { Authorization: `Bearer ${token}` } }),
                fetch('/api/news', { headers: { Authorization: `Bearer ${token}` } }),
                fetch('/api/reports/custom', { headers: { Authorization: `Bearer ${token}` } }),
            ]);
            const prodData = prodRes.ok ? (await prodRes.json()).data || [] : [];
            const newsData = newsRes.ok ? (await newsRes.json()).data || [] : [];
            const customData = customRes.ok ? (await customRes.json()).data || [] : [];

            // Build category-level reports from product data
            const categoryMap = {};
            prodData.forEach(item => {
                const cat = item.category || 'General';
                if (!categoryMap[cat]) categoryMap[cat] = { pos: 0, neg: 0, neu: 0, total: 0 };
                categoryMap[cat].total++;
                if (item.sentiment_label === 'Positive') categoryMap[cat].pos++;
                else if (item.sentiment_label === 'Negative') categoryMap[cat].neg++;
                else categoryMap[cat].neu++;
            });

            const icons = [PieChart, BarChart2, FileText, ExternalLink];
            const colors = ['text-primary', 'text-emerald-400', 'text-amber-400', 'text-violet-400'];
            const today = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });

            const generated = Object.entries(categoryMap).map(([cat, d], i) => ({
                id: i + 1,
                title: `${cat.charAt(0).toUpperCase() + cat.slice(1)} Sentiment Report`,
                date: today,
                tags: [cat, d.pos >= d.neg ? 'Positive Trend' : 'Negative Trend'],
                icon: icons[i % icons.length],
                color: colors[i % colors.length],
                total: d.total,
                pos: d.pos,
                neg: d.neg,
                neu: d.neu,
                posP: d.total > 0 ? Math.round((d.pos / d.total) * 100) : 0,
                category: cat,
            }));

            // Add a news report if we have news data
            if (newsData.length > 0) {
                const nPos = newsData.filter(n => n.sentiment_label === 'Positive').length;
                const nNeg = newsData.filter(n => n.sentiment_label === 'Negative').length;
                const nNeu = newsData.filter(n => n.sentiment_label === 'Neutral').length;
                generated.push({
                    id: generated.length + 1,
                    title: 'News Sentiment Analysis',
                    date: today,
                    tags: ['News', nPos >= nNeg ? 'Positive' : 'Negative'],
                    icon: ExternalLink,
                    color: 'text-violet-400',
                    total: newsData.length,
                    pos: nPos,
                    neg: nNeg,
                    neu: nNeu,
                    posP: newsData.length > 0 ? Math.round((nPos / newsData.length) * 100) : 0,
                    category: 'news',
                });
            }

            setReports(generated);
            setStats({ total: prodData.length, news: newsData.length });
            setRawData({ products: prodData, news: newsData });
            setCustomReports(
                customData.map((r) => ({
                    id: r.id,
                    title: r.title,
                    date: r.created_at ? new Date(r.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }) : 'N/A',
                    tags: r.tags || ['Custom'],
                    icon: FileText,
                    color: 'text-primary',
                    total: r.summary?.total || 0,
                    pos: r.summary?.positive || 0,
                    neg: r.summary?.negative || 0,
                    neu: r.summary?.neutral || 0,
                    posP: (r.summary?.total || 0) > 0 ? Math.round(((r.summary?.positive || 0) / r.summary.total) * 100) : 0,
                    category: `custom-${r.id}`,
                    rows: r.rows || [],
                }))
            );
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const downloadCSV = async (category) => {
        const custom = customReports.find((r) => r.category === category);
        if (custom) {
            exportAsCsv(`${category}_report.csv`, custom.rows || []);
            return;
        }

        const endpoint = category === 'news' ? '/api/news' : '/api/products';
        const res = await apiFetch(endpoint);
        const result = await res.json();
        const data = result.data || [];
        const filtered = category === 'news' ? data : data.filter(d => d.category === category);

        exportAsCsv(`${category}_report.csv`, filtered);
    };

    const batchExport = () => {
        const allReports = [...reports, ...customReports];
        const rows = allReports.map((report) => ({
            title: report.title,
            date: report.date,
            category: report.category,
            total: report.total,
            positive: report.pos,
            neutral: report.neu,
            negative: report.neg,
            positive_percent: report.posP,
        }));
        exportAsCsv('reports_summary.csv', rows);
    };

    const downloadAll = () => {
        const allRows = [
            ...rawData.products.map((row) => ({ type: 'product', ...row })),
            ...rawData.news.map((row) => ({ type: 'news', ...row })),
            ...customReports.flatMap((r) => (r.rows || []).map((row) => ({ type: 'custom', report: r.title, ...row }))),
        ];
        exportAsCsv('all_sentiment_data.csv', allRows);
    };

    const getSentimentCountsFromRows = (rows) => {
        const sentimentKeys = ['sentiment_label', 'sentiment', 'label', 'polarity'];
        let pos = 0;
        let neg = 0;
        let neu = 0;

        rows.forEach((row) => {
            const raw = sentimentKeys.map((k) => row[k]).find((v) => typeof v === 'string') || '';
            const sentiment = String(raw).toLowerCase();
            if (sentiment.includes('pos')) pos += 1;
            else if (sentiment.includes('neg')) neg += 1;
            else neu += 1;
        });

        return { pos, neg, neu, total: rows.length };
    };

    const parseCsvText = (text) => {
        const lines = text.split(/\r?\n/).filter((line) => line.trim());
        if (!lines.length) return [];

        const parseLine = (line) => {
            const cols = [];
            let current = '';
            let inQuotes = false;
            for (let i = 0; i < line.length; i += 1) {
                const ch = line[i];
                if (ch === '"') {
                    if (inQuotes && line[i + 1] === '"') {
                        current += '"';
                        i += 1;
                    } else {
                        inQuotes = !inQuotes;
                    }
                } else if (ch === ',' && !inQuotes) {
                    cols.push(current.trim());
                    current = '';
                } else {
                    current += ch;
                }
            }
            cols.push(current.trim());
            return cols;
        };

        const headers = parseLine(lines[0]).map((h) => h.replace(/^"|"$/g, '').trim());
        return lines.slice(1).map((line) => {
            const values = parseLine(line).map((v) => v.replace(/^"|"$/g, '').trim());
            const row = {};
            headers.forEach((h, idx) => {
                row[h] = values[idx] || '';
            });
            return row;
        });
    };

    const createCustomReport = async (title, tags, rows, source = 'csv') => {
        const created = await apiFetchJSON('/api/reports/custom', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, tags, rows, source }),
        });

        const summary = created.summary || getSentimentCountsFromRows(rows);
        const report = {
            id: created.id,
            title: created.title,
            date: created.created_at ? new Date(created.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }) : new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }),
            tags: created.tags || tags,
            icon: FileText,
            color: 'text-primary',
            total: summary.total || 0,
            pos: summary.positive || 0,
            neg: summary.negative || 0,
            neu: summary.neutral || 0,
            posP: (summary.total || 0) > 0 ? Math.round(((summary.positive || 0) / summary.total) * 100) : 0,
            category: `custom-${created.id}`,
            rows: created.rows || rows,
        };

        setCustomReports((prev) => [report, ...prev]);
        setShowCreateModal(false);
    };

    const handleCsvUpload = async (event) => {
        const file = event.target.files?.[0];
        if (!file) return;

        try {
            setCreating(true);
            const text = await file.text();
            const rows = parseCsvText(text);
            if (!rows.length) throw new Error('CSV file is empty or invalid.');

            await createCustomReport(
                `${file.name.replace(/\.csv$/i, '')} Analysis`,
                ['CSV Upload', 'Custom'],
                rows,
                'csv_upload'
            );
        } catch (err) {
            alert(err.message || 'Failed to import CSV file.');
        } finally {
            event.target.value = '';
            setCreating(false);
        }
    };

    const importFromMarketTrends = async () => {
        if (!rawData.news.length) {
            alert('No Market Trends analysis found yet.');
            return;
        }
        try {
            setCreating(true);
            await createCustomReport('Market Trends Imported Analysis', ['Market Trends', 'Imported'], rawData.news, 'market_trends');
        } catch {
            alert('Failed to persist Market Trends analysis.');
        } finally {
            setCreating(false);
        }
    };

    const importFromTrendingProducts = async () => {
        try {
            setCreating(true);
            const result = await apiFetchJSON('/api/pipeline/latest-data');
            const data = result?.data || [];
            if (!data.length) {
                alert('No Trending Products analysis found yet.');
                return;
            }

            const rows = data.map((item) => ({
                keyword: item.keyword || item.product,
                product: item.product,
                context_type: item.context_type || 'News',
                positive_count: item.positive_count,
                negative_count: item.negative_count,
                neutral_count: item.neutral_count,
                article_count: item.article_count,
                sentiment_label:
                    item.positive_count >= item.negative_count
                        ? 'Positive'
                        : item.negative_count > item.positive_count
                            ? 'Negative'
                            : 'Neutral',
                last_updated: item.last_updated,
            }));

            await createCustomReport('Trending Products Imported Analysis', ['Trending Products', 'Imported'], rows, 'trending_products');
        } catch (err) {
            alert('Failed to import Trending Products analysis.');
        } finally {
            setCreating(false);
        }
    };

    const allReports = [...customReports, ...reports];

    const filteredReports = allReports.filter(r =>
        r.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.tags.some(t => t.toLowerCase().includes(searchQuery.toLowerCase()))
    );

    return (
        <DashboardLayout title="Reports">
            <div className="space-y-10">
                {/* Header */}
                <div className="flex flex-wrap justify-between items-end gap-8">
                    <div className="max-w-2xl">
                        <h1 className="text-4xl font-black text-white tracking-tight mb-3">Reports</h1>
                        <p className="text-slate-400 text-lg leading-relaxed">Manage, export, and analyze your AI-generated sentiment reports.</p>
                    </div>
                    <button onClick={() => { const t = localStorage.getItem('token'); if (t) fetchReports(t); }}
                        className="flex items-center gap-3 px-8 py-4 bg-primary text-background-dark font-black rounded-2xl hover:scale-105 transition-all shadow-xl shadow-primary/20">
                        <Plus className="w-6 h-6" /> Refresh Reports
                    </button>
                </div>

                {/* Filters */}
                <div className="flex flex-col md:flex-row gap-6 items-center justify-between">
                    <div className="relative w-full md:max-w-md group">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-primary transition-colors w-5 h-5" />
                        <input
                            className="w-full pl-12 pr-6 py-4 bg-white/[0.03] border border-white/10 rounded-2xl focus:ring-2 focus:ring-primary/50 outline-none text-sm transition-all"
                            placeholder="Search reports by name or tag..."
                            value={searchQuery}
                            onChange={e => setSearchQuery(e.target.value)}
                        />
                    </div>
                    <div className="flex items-center gap-4 w-full md:w-auto">
                        <div className="flex p-1.5 bg-white/[0.03] border border-white/10 rounded-2xl">
                            {['All', 'Products', 'News'].map((tab) => (
                                <button key={tab} onClick={() => setActiveTab(tab)}
                                    className={`px-6 py-2 rounded-xl text-xs font-black uppercase tracking-widest transition-all ${activeTab === tab ? 'bg-primary text-background-dark' : 'text-slate-500 hover:text-white'}`}>
                                    {tab}
                                </button>
                            ))}
                        </div>
                        <button className="p-4 bg-white/[0.03] border border-white/10 rounded-2xl hover:border-primary/50 transition-all">
                            <Filter className="w-5 h-5 text-primary" />
                        </button>
                    </div>
                </div>

                {/* Grid */}
                {loading ? (
                    <div className="flex items-center justify-center h-64">
                        <Loader2 className="w-12 h-12 text-primary animate-spin" />
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8">
                        {filteredReports
                            .filter(r => activeTab === 'All' || (activeTab === 'News' ? r.category === 'news' : r.category !== 'news'))
                            .map((report, i) => (
                            <motion.div
                                key={report.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: i * 0.08 }}
                                className="group bg-white/[0.02] border border-white/10 p-8 rounded-[2.5rem] hover:border-primary/50 transition-all relative overflow-hidden"
                            >
                                <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 blur-3xl rounded-full translate-x-16 -translate-y-16"></div>
                                <div className="flex justify-between items-start mb-6 relative z-10">
                                    <div className={`p-4 bg-white/5 rounded-2xl ${report.color}`}>
                                        <report.icon className="w-6 h-6" />
                                    </div>
                                    <button onClick={() => downloadCSV(report.category)}
                                        className="p-2 text-slate-500 hover:text-primary transition-colors" title="Download CSV">
                                        <Download className="w-4 h-4" />
                                    </button>
                                </div>
                                <h3 className="font-bold text-xl mb-2 group-hover:text-primary transition-colors">{report.title}</h3>
                                <p className="text-xs text-slate-500 font-medium mb-4">Generated on {report.date} · {report.total} records</p>

                                {/* Sentiment Summary */}
                                <div className="space-y-2 mb-6 bg-white/[0.02] border border-white/10 rounded-xl p-3">
                                    <div className="flex justify-between text-xs">
                                        <span className="text-slate-400">Positive</span>
                                        <span className="text-emerald-400 font-bold">{report.posP}%</span>
                                    </div>
                                    <div className="flex justify-between text-xs">
                                        <span className="text-slate-400">Negative</span>
                                        <span className="text-rose-400 font-bold">{report.total > 0 ? Math.round((report.neg / report.total) * 100) : 0}%</span>
                                    </div>
                                    <div className="flex justify-between text-xs">
                                        <span className="text-slate-400">Neutral</span>
                                        <span className="text-slate-400 font-bold">{report.total > 0 ? Math.round((report.neu / report.total) * 100) : 0}%</span>
                                    </div>
                                </div>

                                <div className="flex flex-wrap gap-2 mb-6">
                                    {report.tags.map(tag => (
                                        <span key={tag} className="px-3 py-1 bg-white/5 border border-white/5 text-[10px] font-black rounded-lg uppercase tracking-wider text-slate-400">{tag}</span>
                                    ))}
                                </div>
                                <button onClick={() => downloadCSV(report.category)}
                                    className="w-full py-3 bg-white/5 border border-white/10 hover:bg-primary hover:text-background-dark font-black rounded-2xl text-xs uppercase tracking-[0.2em] transition-all">
                                    Download CSV
                                </button>
                            </motion.div>
                        ))}

                        {/* New Analysis Card */}
                        <div onClick={() => setShowCreateModal(true)}
                            className="border-2 border-dashed border-white/10 rounded-[2.5rem] p-8 flex flex-col items-center justify-center text-center gap-6 group hover:border-primary/50 transition-all cursor-pointer">
                            <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center text-slate-600 group-hover:text-primary group-hover:bg-primary/10 transition-all duration-500">
                                <Plus className="w-8 h-8" />
                            </div>
                            <div>
                                <p className="font-bold text-lg text-white">New Sentiment Analysis</p>
                                <p className="text-sm text-slate-500 mt-1">Upload CSV or import from existing trend analyses</p>
                            </div>
                            <span className="text-[10px] font-black text-primary uppercase tracking-widest">Create Analysis →</span>
                        </div>
                    </div>
                )}

                {/* Footer Stats */}
                <div className="bg-white/[0.02] border border-white/10 p-10 rounded-[3rem] flex flex-wrap items-center justify-between gap-10">
                    <div className="flex items-center gap-12">
                        {[
                            { label: 'Total Product Reviews', val: loading ? '...' : String(stats.total) },
                            { label: 'News Articles', val: loading ? '...' : String(stats.news) },
                            { label: 'Generated Reports', val: loading ? '...' : String(reports.length) },
                        ].map(stat => (
                            <div key={stat.label}>
                                <p className="text-[10px] uppercase font-black tracking-[0.2em] text-slate-500 mb-2">{stat.label}</p>
                                <p className="text-3xl font-black">{stat.val}</p>
                            </div>
                        ))}
                    </div>
                    <div className="flex gap-4">
                        <button onClick={batchExport} className="px-8 py-4 bg-white/5 border border-white/10 rounded-2xl text-xs font-black uppercase tracking-widest hover:bg-white/10 transition-all">Batch Export</button>
                        <button onClick={downloadAll} className="px-8 py-4 bg-white text-background-dark rounded-2xl text-xs font-black uppercase tracking-widest hover:scale-105 transition-all">Download All (CSV)</button>
                    </div>
                </div>

                {/* Create Analysis Modal */}
                {showCreateModal && (
                    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-6">
                        <div className="w-full max-w-2xl bg-slate-950 border border-white/10 rounded-3xl p-8 space-y-6 relative">
                            <button
                                onClick={() => setShowCreateModal(false)}
                                className="absolute top-4 right-4 p-2 rounded-lg hover:bg-white/10 text-slate-400"
                            >
                                <X className="w-5 h-5" />
                            </button>

                            <div>
                                <h3 className="text-2xl font-black text-white">Create New Analysis</h3>
                                <p className="text-slate-400 mt-2">Choose one source to generate a new report card.</p>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <label className="cursor-pointer border border-white/10 rounded-2xl p-5 bg-white/5 hover:border-primary/50 transition-all">
                                    <div className="flex items-start gap-3">
                                        <Upload className="w-5 h-5 text-primary mt-0.5" />
                                        <div>
                                            <p className="font-bold text-white">Upload CSV From Laptop</p>
                                            <p className="text-xs text-slate-400 mt-1">Import your own sentiment file and create a report.</p>
                                        </div>
                                    </div>
                                    <input type="file" accept=".csv" className="hidden" onChange={handleCsvUpload} />
                                </label>

                                <button
                                    onClick={importFromMarketTrends}
                                    disabled={creating}
                                    className="text-left border border-white/10 rounded-2xl p-5 bg-white/5 hover:border-primary/50 transition-all disabled:opacity-50"
                                >
                                    <p className="font-bold text-white">Import From Market Trends</p>
                                    <p className="text-xs text-slate-400 mt-1">Use existing analysis generated in Market Trends section.</p>
                                </button>

                                <button
                                    onClick={importFromTrendingProducts}
                                    disabled={creating}
                                    className="text-left border border-white/10 rounded-2xl p-5 bg-white/5 hover:border-primary/50 transition-all md:col-span-2 disabled:opacity-50"
                                >
                                    <p className="font-bold text-white">Import From Trending Products</p>
                                    <p className="text-xs text-slate-400 mt-1">Use latest analysis from Trending Products section immediately.</p>
                                </button>
                            </div>

                            {creating && (
                                <div className="flex items-center gap-2 text-sm text-slate-400">
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    Creating analysis report...
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </DashboardLayout>
    );
};

export default Reports;
