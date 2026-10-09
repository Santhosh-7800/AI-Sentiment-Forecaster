import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, AlertCircle, FileText, BarChart3, Brain, Zap } from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';
import { apiFetch } from '../lib/api';

const Analytics = () => {
    const [analyses, setAnalyses] = useState([]);
    const [alerts, setAlerts] = useState([]);
    const [alertStats, setAlertStats] = useState({ total_active: 0, critical: 0, warning: 0 });
    const [loading, setLoading] = useState(true);
    const [selectedProduct, setSelectedProduct] = useState(null);
    const [reports, setReports] = useState([]);

    useEffect(() => {
        loadAnalytics();
    }, []);

    const loadAnalytics = async () => {
        try {
            setLoading(true);
            
            // Load active alerts
            const alertsResponse = await apiFetch('/api/analytics/alerts/active');
            if (alertsResponse.ok) {
                const alertsData = await alertsResponse.json();
                setAlerts(alertsData.alerts || []);
            }

            // Load alert stats
            const statsResponse = await apiFetch('/api/analytics/alerts/stats');
            if (statsResponse.ok) {
                const statsData = await statsResponse.json();
                setAlertStats(statsData.data || {});
            }

        } catch (error) {
            console.error('Error loading analytics:', error);
        } finally {
            setLoading(false);
        }
    };

    const generateReport = async (format) => {
        try {
            const response = await apiFetch('/api/analytics/reports/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    product: selectedProduct || 'Summary',
                    analysis_data: {},
                    format: format
                })
            });

            if (response.ok) {
                const data = await response.json();
                alert(`${format.toUpperCase()} report generated successfully!`);
                // In a real app, would download the file
            }
        } catch (error) {
            console.error('Report generation error:', error);
        }
    };

    return (
        <DashboardLayout title="Advanced Analytics">
            <div className="space-y-8">
                {/* Header */}
                <div>
                    <h1 className="text-4xl font-black text-white tracking-tight">Advanced Analytics Suite</h1>
                    <p className="text-slate-400 mt-2 text-lg">
                        Sentiment trends, topic modeling, alerts, and insights
                    </p>
                </div>

                {/* Alert Summary */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="grid grid-cols-1 md:grid-cols-4 gap-4"
                >
                    <div className="bg-white/[0.03] border border-white/10 rounded-[2rem] p-6">
                        <div className="flex items-center gap-3 mb-3">
                            <AlertCircle className="w-6 h-6 text-primary" />
                            <span className="text-sm font-bold text-slate-400">CRITICAL ALERTS</span>
                        </div>
                        <div className="text-3xl font-black text-white">{alertStats.critical || 0}</div>
                    </div>

                    <div className="bg-white/[0.03] border border-white/10 rounded-[2rem] p-6">
                        <div className="flex items-center gap-3 mb-3">
                            <TrendingUp className="w-6 h-6 text-yellow-500" />
                            <span className="text-sm font-bold text-slate-400">WARNINGS</span>
                        </div>
                        <div className="text-3xl font-black text-white">{alertStats.warning || 0}</div>
                    </div>

                    <div className="bg-white/[0.03] border border-white/10 rounded-[2rem] p-6">
                        <div className="flex items-center gap-3 mb-3">
                            <Brain className="w-6 h-6 text-purple-500" />
                            <span className="text-sm font-bold text-slate-400">TOPICS</span>
                        </div>
                        <div className="text-3xl font-black text-white">5</div>
                    </div>

                    <div className="bg-white/[0.03] border border-white/10 rounded-[2rem] p-6">
                        <div className="flex items-center gap-3 mb-3">
                            <Zap className="w-6 h-6 text-orange-500" />
                            <span className="text-sm font-bold text-slate-400">SPIKES</span>
                        </div>
                        <div className="text-3xl font-black text-white">3</div>
                    </div>
                </motion.div>

                {/* Active Alerts */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-white/[0.03] border border-white/10 rounded-[3rem] p-8"
                >
                    <div className="flex items-center gap-3 mb-6">
                        <AlertCircle className="w-6 h-6 text-primary" />
                        <h2 className="text-2xl font-bold">Active Alerts</h2>
                    </div>

                    {alerts.length === 0 ? (
                        <p className="text-slate-400">No active alerts</p>
                    ) : (
                        <div className="space-y-3">
                            {alerts.slice(0, 5).map((alert) => (
                                <div
                                    key={alert.id}
                                    className={`p-4 rounded-2xl border ${
                                        alert.severity === 'critical'
                                            ? 'bg-red-500/10 border-red-500/20'
                                            : 'bg-yellow-500/10 border-yellow-500/20'
                                    }`}
                                >
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <p className="font-bold text-white">{alert.message}</p>
                                            <p className="text-sm text-slate-400 mt-1">
                                                Product: {alert.product} • {new Date(alert.timestamp).toLocaleDateString()}
                                            </p>
                                        </div>
                                        <span className={`px-3 py-1 rounded-lg font-bold text-xs ${
                                            alert.severity === 'critical' ? 'bg-red-500/20 text-red-300' : 'bg-yellow-500/20 text-yellow-300'
                                        }`}>
                                            {alert.severity.toUpperCase()}
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </motion.div>

                {/* Analytics Features Grid */}
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="grid grid-cols-1 md:grid-cols-2 gap-8"
                >
                    {/* Sentiment Analysis */}
                    <div className="bg-white/[0.03] border border-white/10 rounded-[3rem] p-8">
                        <div className="flex items-center gap-3 mb-6">
                            <Brain className="w-6 h-6 text-primary" />
                            <h3 className="text-xl font-bold">Enhanced Sentiment</h3>
                        </div>
                        <p className="text-slate-400 mb-4">
                            Advanced sentiment analysis with emotion detection and aspect-based insights
                        </p>
                        <ul className="space-y-2 text-sm mb-6">
                            <li className="flex items-center gap-2">
                                <span className="w-2 h-2 bg-primary rounded-full"></span>
                                Emotion detection (joy, anger, sadness)
                            </li>
                            <li className="flex items-center gap-2">
                                <span className="w-2 h-2 bg-primary rounded-full"></span>
                                Aspect-based sentiment analysis
                            </li>
                            <li className="flex items-center gap-2">
                                <span className="w-2 h-2 bg-primary rounded-full"></span>
                                Confidence scoring
                            </li>
                        </ul>
                        <button className="w-full bg-primary text-background-dark font-bold py-3 rounded-2xl hover:brightness-110 active:scale-95 transition-all">
                            Analyze Sentiment
                        </button>
                    </div>

                    {/* Topic Modeling */}
                    <div className="bg-white/[0.03] border border-white/10 rounded-[3rem] p-8">
                        <div className="flex items-center gap-3 mb-6">
                            <BarChart3 className="w-6 h-6 text-purple-500" />
                            <h3 className="text-xl font-bold">Topic Modeling</h3>
                        </div>
                        <p className="text-slate-400 mb-4">
                            Extract emerging topics and track how they evolve over time
                        </p>
                        <ul className="space-y-2 text-sm mb-6">
                            <li className="flex items-center gap-2">
                                <span className="w-2 h-2 bg-purple-500 rounded-full"></span>
                                 Automatic topic extraction
                            </li>
                            <li className="flex items-center gap-2">
                                <span className="w-2 h-2 bg-purple-500 rounded-full"></span>
                                Topic evolution tracking
                            </li>
                            <li className="flex items-center gap-2">
                                <span className="w-2 h-2 bg-purple-500 rounded-full"></span>
                                Keyword identification
                            </li>
                        </ul>
                        <button className="w-full bg-purple-600 text-white font-bold py-3 rounded-2xl hover:brightness-110 active:scale-95 transition-all">
                            Extract Topics
                        </button>
                    </div>

                    {/* Trend Analysis */}
                    <div className="bg-white/[0.03] border border-white/10 rounded-[3rem] p-8">
                        <div className="flex items-center gap-3 mb-6">
                            <TrendingUp className="w-6 h-6 text-green-500" />
                            <h3 className="text-xl font-bold">Trend Analysis</h3>
                        </div>
                        <p className="text-slate-400 mb-4">
                            Analyze sentiment trends with forecasting and anomaly detection
                        </p>
                        <ul className="space-y-2 text-sm mb-6">
                            <li className="flex items-center gap-2">
                                <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                                Trend direction analysis
                            </li>
                            <li className="flex items-center gap-2">
                                <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                                30-day sentiment forecast
                            </li>
                            <li className="flex items-center gap-2">
                                <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                                Anomaly spike detection
                            </li>
                        </ul>
                        <button className="w-full bg-green-600 text-white font-bold py-3 rounded-2xl hover:brightness-110 active:scale-95 transition-all">
                            Analyze Trends
                        </button>
                    </div>

                    {/* Report Generation */}
                    <div className="bg-white/[0.03] border border-white/10 rounded-[3rem] p-8">
                        <div className="flex items-center gap-3 mb-6">
                            <FileText className="w-6 h-6 text-orange-500" />
                            <h3 className="text-xl font-bold">Report Generation</h3>
                        </div>
                        <p className="text-slate-400 mb-4">
                            Generate professional PDF and Excel reports
                        </p>
                        <ul className="space-y-2 text-sm mb-6">
                            <li className="flex items-center gap-2">
                                <span className="w-2 h-2 bg-orange-500 rounded-full"></span>
                                PDF reports with charts
                            </li>
                            <li className="flex items-center gap-2">
                                <span className="w-2 h-2 bg-orange-500 rounded-full"></span>
                                Excel exports with metrics
                            </li>
                            <li className="flex items-center gap-2">
                                <span className="w-2 h-2 bg-orange-500 rounded-full"></span>
                                Batch product comparison
                            </li>
                        </ul>
                        <div className="space-y-2">
                            <button 
                                onClick={() => generateReport('pdf')}
                                className="w-full bg-orange-600 text-white font-bold py-2 rounded-xl hover:brightness-110 active:scale-95 transition-all text-sm"
                            >
                                Generate PDF
                            </button>
                            <button 
                                onClick={() => generateReport('excel')}
                                className="w-full bg-orange-700 text-white font-bold py-2 rounded-xl hover:brightness-110 active:scale-95 transition-all text-sm"
                            >
                                Generate Excel
                            </button>
                        </div>
                    </div>
                </motion.div>

                {/* Sample Analytics Output */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-white/[0.03] border border-white/10 rounded-[3rem] p-8"
                >
                    <h2 className="text-2xl font-bold mb-6">Analytics API Documentation</h2>
                    <p className="text-slate-400 mb-4">
                        All analytics features are available via REST API endpoints. Access the interactive API documentation at:
                    </p>
                    <code className="block bg-black/50 p-4 rounded-xl text-primary font-mono text-sm mb-4 overflow-auto">
                        GET http://localhost:8000/docs
                    </code>
                    <p className="text-slate-400 text-sm">
                        Endpoints include: sentiment analysis, topic extraction, trend forecasting, alert management, and report generation.
                    </p>
                </motion.div>
            </div>
        </DashboardLayout>
    );
};

export default Analytics;
