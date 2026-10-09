import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Zap, AlertCircle, CheckCircle } from 'lucide-react';
import { apiFetchJSON } from '../lib/api';

const PipelineStatus = () => {
    const [status, setStatus] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        fetchPipelineStatus();
        // Auto-refresh every 5 minutes
        const interval = setInterval(fetchPipelineStatus, 300000);
        return () => clearInterval(interval);
    }, []);

    const fetchPipelineStatus = async () => {
        try {
            const result = await apiFetchJSON('/api/pipeline/status');
            if (result.success) {
                setStatus(result.pipeline);
                setError('');
            }
        } catch (err) {
            console.error('Error fetching pipeline status:', err);
            setError('Unable to fetch pipeline status');
        } finally {
            setLoading(false);
        }
    };

    if (loading || !status) {
        return null;
    }

    const newsapiQuota = status.quota_status?.newsapi;
    const isRunning = status.running;
    const newsapiExhausted = newsapiQuota?.exhausted;
    const newsapiRemaining = newsapiQuota?.remaining;

    return (
        <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white/[0.02] border border-white/10 rounded-2xl p-4 text-sm"
        >
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    {isRunning ? (
                        <>
                            <CheckCircle className="w-5 h-5 text-emerald-400" />
                            <span className="text-slate-300">
                                Pipeline is <span className="text-emerald-400 font-bold">running</span>
                            </span>
                        </>
                    ) : (
                        <>
                            <AlertCircle className="w-5 h-5 text-yellow-500" />
                            <span className="text-slate-300">
                                Pipeline is <span className="text-yellow-500 font-bold">inactive</span>
                            </span>
                        </>
                    )}
                </div>

                {newsapiQuota && (
                    <div className="flex items-center gap-2">
                        {newsapiExhausted ? (
                            <div className="flex items-center gap-2 px-3 py-1 bg-rose-500/10 border border-rose-500/30 rounded-lg">
                                <AlertCircle className="w-4 h-4 text-rose-400" />
                                <span className="text-rose-300 text-xs font-bold">NewsAPI quota exhausted</span>
                            </div>
                        ) : (
                            <div className="flex items-center gap-2 px-3 py-1 bg-emerald-500/10 border border-emerald-500/30 rounded-lg">
                                <CheckCircle className="w-4 h-4 text-emerald-400" />
                                <span className="text-emerald-300 text-xs">
                                    NewsAPI: <span className="font-bold">{newsapiRemaining}</span> requests left today
                                </span>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </motion.div>
    );
};

export default PipelineStatus;
