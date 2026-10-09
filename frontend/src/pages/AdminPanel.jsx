import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ShieldCheck, Users, Box, BarChart, MessageSquare, Search, Bell, Activity, UserPlus, MoreVertical, ChevronLeft, ChevronRight, TrendingUp } from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';

const AdminPanel = () => {
    const navigate = useNavigate();
    const [apiStats, setApiStats] = useState(null);
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token) { navigate('/login'); return; }

        const isAdmin = localStorage.getItem('is_admin') === 'true';
        if (!isAdmin) { navigate('/dashboard'); return; }

        Promise.all([
            fetch('/api/stats').then(r => r.json()),
            fetch('/api/admin/users', { headers: { Authorization: `Bearer ${token}` } }).then(async (r) => {
                if (r.status === 401) {
                    localStorage.removeItem('token');
                    localStorage.removeItem('is_admin');
                    navigate('/login');
                    return { users: [] };
                }
                if (r.status === 403) {
                    navigate('/dashboard');
                    return { users: [] };
                }
                return r.json();
            }),
        ]).then(([statsData, usersData]) => {
            setApiStats(statsData);
            if (usersData.users) {
                const colors = ['bg-primary', 'bg-violet-500', 'bg-amber-500', 'bg-emerald-500', 'bg-rose-500'];
                setUsers(usersData.users.map((u, i) => ({
                    name: `${u.firstname || ''} ${u.lastname || ''}`.trim() || u.email,
                    email: u.email,
                    status: 'Active',
                    plan: 'Free Tier',
                    lastActive: 'Recently',
                    initial: (u.firstname?.[0] || u.email?.[0] || '?').toUpperCase(),
                    color: colors[i % colors.length],
                })));
            }
        }).catch(console.error).finally(() => setLoading(false));
    }, [navigate]);

    const stats = [
        { label: 'Total Reviews', val: loading ? '...' : String(apiStats?.total_reviews ?? 0), trend: 0.2, icon: Activity, color: 'text-emerald-400' },
        { label: 'Registered Users', val: loading ? '...' : String(apiStats?.total_users ?? 0), trend: 12.5, icon: Users, color: 'text-primary' },
        { label: 'News Articles', val: loading ? '...' : String(apiStats?.total_news ?? 0), trend: 8.1, icon: BarChart, color: 'text-amber-400' },
        { label: 'Avg. Sentiment', val: loading ? '...' : (apiStats?.dominant_sentiment ?? 'Neutral'), trend: 4.2, icon: MessageSquare, color: 'text-violet-400' },
    ];

    return (
        <DashboardLayout title="Admin Panel">
            <div className="space-y-12 pb-20">
                {/* Header */}
                <div className="flex flex-wrap items-center justify-between gap-8">
                    <div>
                        <h1 className="text-4xl font-black text-white tracking-tight flex items-center gap-4">
                            <ShieldCheck className="w-10 h-10 text-primary" /> Admin Panel
                        </h1>
                        <p className="text-slate-400 text-lg mt-2">Real-time performance and engagement metrics</p>
                    </div>
                    <div className="flex items-center gap-6">
                        <div className="relative group">
                            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-primary transition-colors" />
                            <input
                                className="pl-12 pr-6 py-4 bg-white/[0.03] border border-white/10 rounded-2xl focus:ring-2 focus:ring-primary/50 outline-none text-sm w-80 transition-all font-medium"
                                placeholder="Search global data..."
                            />
                        </div>
                        <button className="p-4 bg-white/[0.03] border border-white/10 rounded-2xl relative">
                            <Bell className="w-6 h-6 text-slate-400" />
                            <span className="absolute top-3 right-3 w-3 h-3 bg-primary rounded-full border-4 border-background-dark shadow-[0_0_10px_rgba(13,204,242,0.5)]"></span>
                        </button>
                    </div>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                    {stats.map((stat, i) => (
                        <motion.div
                            key={stat.label}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.1 }}
                            className="bg-white/[0.03] border border-white/10 p-10 rounded-[3rem] group relative overflow-hidden"
                        >
                            <div className="absolute top-0 right-0 w-24 h-24 bg-primary/5 blur-3xl rounded-full translate-x-12 -translate-y-12"></div>
                            <div className="flex items-center justify-between mb-8">
                                <div className={`p-4 bg-white/5 rounded-2xl ${stat.color}`}>
                                    <stat.icon className="w-6 h-6" />
                                </div>
                                <span className="text-xs font-black text-emerald-400 bg-emerald-400/10 px-3 py-1 rounded-full border border-emerald-400/20">+{stat.trend}%</span>
                            </div>
                            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500 mb-2">{stat.label}</p>
                            <p className="text-3xl font-black text-white">{stat.val}</p>
                        </motion.div>
                    ))}
                </div>

                {/* User Table */}
                <div className="bg-white/[0.03] border border-white/10 rounded-[3.5rem] overflow-hidden shadow-2xl relative">
                    <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-white/5 to-transparent"></div>
                    <div className="p-10 border-b border-white/5 flex items-center justify-between bg-white/[0.01]">
                        <div>
                            <h3 className="text-2xl font-black text-white">Platform Community</h3>
                            <p className="text-slate-500 font-medium mt-1">Manage all active and inactive users</p>
                        </div>
                        <button className="bg-primary text-background-dark px-8 py-4 rounded-2xl font-black text-sm hover:scale-105 transition-all shadow-xl shadow-primary/20 flex items-center gap-3">
                            <UserPlus className="w-5 h-5" /> Invite New User
                        </button>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead>
                                <tr className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500 bg-white/[0.02]">
                                    <th className="px-10 py-6">User Identity</th>
                                    <th className="px-10 py-6">Status</th>
                                    <th className="px-10 py-6">Subscription</th>
                                    <th className="px-10 py-6">Last Activity</th>
                                    <th className="px-10 py-6 text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/5">
                                {users.map((user) => (
                                    <tr key={user.name} className="hover:bg-white/[0.02] transition-colors group">
                                        <td className="px-10 py-8">
                                            <div className="flex items-center gap-5">
                                                <div className={`w-14 h-14 rounded-2xl ${user.color} flex items-center justify-center text-background-dark font-black text-lg shadow-lg shadow-inherit/20`}>
                                                    {user.initial}
                                                </div>
                                                <div>
                                                    <p className="font-bold text-lg text-white group-hover:text-primary transition-colors">{user.name}</p>
                                                    <p className="text-sm text-slate-500 mt-1 font-medium">{user.email}</p>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-10 py-8">
                                            <div className="flex items-center gap-2">
                                                <span className={`w-2 h-2 rounded-full ${user.status === 'Active' ? 'bg-emerald-400 animate-pulse' : 'bg-slate-600'}`}></span>
                                                <span className={`text-[10px] font-black uppercase tracking-widest ${user.status === 'Active' ? 'text-emerald-400' : 'text-slate-500'}`}>{user.status}</span>
                                            </div>
                                        </td>
                                        <td className="px-10 py-8">
                                            <span className="px-4 py-1.5 rounded-xl bg-white/5 border border-white/5 text-[10px] font-black uppercase tracking-widest text-slate-300">
                                                {user.plan}
                                            </span>
                                        </td>
                                        <td className="px-10 py-8 text-sm font-bold text-slate-500">{user.lastActive}</td>
                                        <td className="px-10 py-8 text-right">
                                            <button className="p-3 hover:bg-white/5 rounded-xl transition-colors text-slate-500 hover:text-white">
                                                <MoreVertical className="w-5 h-5" />
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                    <div className="p-8 border-t border-white/5 flex items-center justify-between bg-white/[0.01]">
                        <p className="text-xs font-black uppercase tracking-widest text-slate-600">Showing {users.length} of {loading ? '...' : (apiStats?.total_users ?? users.length)} members</p>
                        <div className="flex items-center gap-4">
                            <button className="p-3 bg-white/5 rounded-2xl text-slate-500 hover:text-white disabled:opacity-30" disabled>
                                <ChevronLeft className="w-5 h-5" />
                            </button>
                            <button className="p-3 bg-white/5 border border-white/10 rounded-2xl text-slate-500 hover:text-white hover:border-primary/50 transition-all">
                                <ChevronRight className="w-5 h-5" />
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
};

export default AdminPanel;
