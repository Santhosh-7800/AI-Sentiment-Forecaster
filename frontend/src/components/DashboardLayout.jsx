import React from 'react';
import Sidebar from './Sidebar';
import { Bell, MessageSquare, LogOut, Search } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const DashboardLayout = ({ children, title = "Dashboard" }) => {
    const navigate = useNavigate();

    const handleLogout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('is_admin');
        navigate('/login');
    };

    return (
        <div className="flex h-screen bg-background-dark overflow-hidden">
            <Sidebar />

            <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
                {/* Header */}
                <header className="h-20 flex items-center justify-between px-8 border-b border-white/5 bg-background-dark/50 backdrop-blur-xl sticky top-0 z-20">
                    <div className="flex items-center gap-4">
                        <h2 className="text-white text-lg font-bold tracking-tight">{title}</h2>
                        <span className="bg-primary/10 text-primary text-[10px] px-2.5 py-1 rounded-full font-black uppercase tracking-widest border border-primary/20">
                            Live
                        </span>
                    </div>

                    <div className="flex items-center gap-4">
                        <button className="p-2.5 rounded-xl bg-white/5 text-slate-400 hover:bg-white/10 hover:text-primary transition-all relative">
                            <Bell className="w-5 h-5" />
                            <span className="absolute top-2 right-2 w-2 h-2 bg-primary rounded-full border-2 border-background-dark"></span>
                        </button>
                        <button className="p-2.5 rounded-xl bg-white/5 text-slate-400 hover:bg-white/10 hover:text-primary transition-all">
                            <MessageSquare className="w-5 h-5" />
                        </button>

                        <div className="h-8 w-px bg-white/10 mx-2"></div>

                        <button onClick={handleLogout} className="flex items-center gap-3 group px-2 py-1.5 rounded-xl hover:bg-white/5 transition-all">
                            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-primary to-blue-500 p-[1px]">
                                <div className="w-full h-full rounded-full bg-background-dark flex items-center justify-center overflow-hidden">
                                    <img
                                        src="https://i.pravatar.cc/150?u=dashboard"
                                        className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity"
                                        alt="User"
                                    />
                                </div>
                            </div>
                            <div className="hidden sm:flex flex-col">
                                <span className="text-xs font-bold text-slate-200">My Account</span>
                                <span className="text-[10px] text-slate-500 font-medium">Sign Out</span>
                            </div>
                            <LogOut className="w-4 h-4 text-slate-500 group-hover:text-red-400 transition-colors ml-1" />
                        </button>
                    </div>
                </header>

                {/* Content */}
                <div className="flex-1 overflow-y-auto custom-scrollbar p-8">
                    <div className="max-w-7xl mx-auto space-y-10">
                        {children}
                    </div>
                </div>
            </main>
        </div>
    );
};

export default DashboardLayout;
