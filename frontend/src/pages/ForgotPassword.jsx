<<<<<<< HEAD

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BarChart3, Mail, Lock, ArrowRight, ShieldCheck, CheckCircle2 } from 'lucide-react';
import { NavLink, useNavigate } from 'react-router-dom';
import ThemeToggle from '../components/ThemeToggle';

const ForgotPassword = () => {
    const navigate = useNavigate();
    
    // States
    const [step, setStep] = useState(1); 
    const [email, setEmail] = useState("");
    const [otp, setOtp] = useState("");
    const [newPassword, setNewPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState({ type: '', text: '' });

    const handleRequestOTP = async (e) => {
        e.preventDefault();
        setLoading(true);
        setMessage({ type: '', text: '' });

        try {
            const res = await fetch("/api/auth/request-otp", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email })
            });
            const data = await res.json();

            if (res.ok) {
                setStep(2);
                setMessage({ type: 'success', text: 'OTP sent! Please check your inbox.' });
            } else {
                setMessage({ type: 'error', text: data.detail || 'User not found.' });
            }
        } catch (err) {
            setMessage({ type: 'error', text: 'Server error. Try again later.' });
        } finally {
            setLoading(false);
        }
    };

    
    const handleResetPassword = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const res = await fetch("/api/auth/verify-reset", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, otp, new_password: newPassword })
            });
            const data = await res.json();

            if (res.ok) {
                setMessage({ type: 'success', text: 'Password reset successful! Redirecting...' });
                setTimeout(() => navigate('/login'), 3000);
            } else {
                setMessage({ type: 'error', text: data.detail || 'Invalid OTP.' });
            }
        } catch (err) {
            setMessage({ type: 'error', text: 'Reset failed.' });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] flex items-center justify-center p-6 relative overflow-hidden">
            
            <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-primary/10 rounded-full blur-[120px]"></div>
            
            <div className="absolute top-6 right-6 z-50">
                <ThemeToggle />
            </div>

            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md z-10">
                <div className="flex flex-col items-center gap-8 bg-white/5 border border-white/10 p-10 rounded-[2.5rem] backdrop-blur-xl shadow-2xl relative">
                    
                    <NavLink to="/" className="flex items-center gap-3">
                        <BarChart3 className="w-10 h-10 text-primary" />
                        <h1 className="text-2xl font-bold">TrendAI</h1>
                    </NavLink>

                    <div className="text-center">
                        <h2 className="text-3xl font-bold mb-2">
                            {step === 1 ? "Reset Password" : "Check Your Email"}
                        </h2>
                        <p className="text-[var(--text-secondary)]">
                            {step === 1 
                                ? "Enter your email to receive a 6-digit verification code" 
                                : `Enter the code sent to ${email}`}
                        </p>
                    </div>

                    {message.text && (
                        <div className={`w-full p-3 rounded-xl text-sm text-center flex items-center justify-center gap-2 ${
                            message.type === 'success' ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-red-500/10 text-red-500 border border-red-500/20'
                        }`}>
                            {message.type === 'success' && <CheckCircle2 className="w-4 h-4" />}
                            {message.text}
                        </div>
                    )}

                    <AnimatePresence mode="wait">
                        {step === 1 ? (
                            <motion.form 
                                key="step1" 
                                initial={{ opacity: 0, x: -20 }} 
                                animate={{ opacity: 1, x: 0 }} 
                                exit={{ opacity: 0, x: 20 }}
                                className="w-full flex flex-col gap-6" 
                                onSubmit={handleRequestOTP}
                            >
                                <div className="relative group">
                                    <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--text-secondary)]" />
                                    <input
                                        type="email"
                                        placeholder="Enter your email"
                                        required
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        className="w-full bg-white/5 border border-white/10 rounded-2xl py-4 pl-12 pr-4 outline-none focus:border-primary/50 text-lg transition-all"
                                    />
                                </div>
                                <button type="submit" disabled={loading} className="bg-primary text-white py-4 rounded-2xl font-bold flex justify-center items-center gap-2 hover:brightness-110 disabled:opacity-50">
                                    {loading ? "Sending..." : "Send Code"} <ArrowRight className="w-5 h-5" />
                                </button>
                            </motion.form>
                        ) : (
                            <motion.form 
                                key="step2" 
                                initial={{ opacity: 0, x: 20 }} 
                                animate={{ opacity: 1, x: 0 }} 
                                exit={{ opacity: 0, x: -20 }}
                                className="w-full flex flex-col gap-6" 
                                onSubmit={handleResetPassword}
                            >
                                <div className="flex flex-col gap-4">
                                    <div className="relative group">
                                        <ShieldCheck className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-primary" />
                                        <input
                                            type="text"
                                            maxLength="6"
                                            placeholder="6-digit OTP"
                                            required
                                            value={otp}
                                            onChange={(e) => setOtp(e.target.value)}
                                            className="w-full bg-white/5 border border-white/10 rounded-2xl py-4 pl-12 text-center text-xl tracking-[0.3em] font-bold outline-none focus:border-primary"
                                        />
                                    </div>
                                    <div className="relative group">
                                        <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--text-secondary)]" />
                                        <input
                                            type="password"
                                            placeholder="New Password"
                                            required
                                            value={newPassword}
                                            onChange={(e) => setNewPassword(e.target.value)}
                                            className="w-full bg-white/5 border border-white/10 rounded-2xl py-4 pl-12 pr-4 outline-none focus:border-primary/50 text-lg"
                                        />
                                    </div>
                                </div>
                                <button type="submit" disabled={loading} className="bg-primary text-white py-4 rounded-2xl font-bold flex justify-center items-center gap-2 hover:brightness-110">
                                    {loading ? "Resetting..." : "Reset Password"} <ArrowRight className="w-5 h-5" />
                                </button>
                                <button type="button" onClick={() => setStep(1)} className="text-sm text-[var(--text-secondary)] hover:text-primary transition-colors text-center">
                                    Resend Code
                                </button>
                            </motion.form>
                        )}
                    </AnimatePresence>

                    <div className="mt-4">
                        <NavLink to="/login" className="text-primary font-bold hover:underline flex items-center gap-2">
                             Back to Login
                        </NavLink>
                    </div>
                </div>
            </motion.div>
        </div>
    );
};

=======

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BarChart3, Mail, Lock, ArrowRight, ShieldCheck, CheckCircle2 } from 'lucide-react';
import { NavLink, useNavigate } from 'react-router-dom';
import ThemeToggle from '../components/ThemeToggle';

const ForgotPassword = () => {
    const navigate = useNavigate();
    
    // States
    const [step, setStep] = useState(1); 
    const [email, setEmail] = useState("");
    const [otp, setOtp] = useState("");
    const [newPassword, setNewPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState({ type: '', text: '' });

    const handleRequestOTP = async (e) => {
        e.preventDefault();
        setLoading(true);
        setMessage({ type: '', text: '' });

        try {
            const res = await fetch("/api/auth/request-otp", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email })
            });
            const data = await res.json();

            if (res.ok) {
                setStep(2);
                setMessage({ type: 'success', text: 'OTP sent! Please check your inbox.' });
            } else {
                setMessage({ type: 'error', text: data.detail || 'User not found.' });
            }
        } catch (err) {
            setMessage({ type: 'error', text: 'Server error. Try again later.' });
        } finally {
            setLoading(false);
        }
    };

    
    const handleResetPassword = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const res = await fetch("/api/auth/verify-reset", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, otp, new_password: newPassword })
            });
            const data = await res.json();

            if (res.ok) {
                setMessage({ type: 'success', text: 'Password reset successful! Redirecting...' });
                setTimeout(() => navigate('/login'), 3000);
            } else {
                setMessage({ type: 'error', text: data.detail || 'Invalid OTP.' });
            }
        } catch (err) {
            setMessage({ type: 'error', text: 'Reset failed.' });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] flex items-center justify-center p-6 relative overflow-hidden">
            
            <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-primary/10 rounded-full blur-[120px]"></div>
            
            <div className="absolute top-6 right-6 z-50">
                <ThemeToggle />
            </div>

            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md z-10">
                <div className="flex flex-col items-center gap-8 bg-white/5 border border-white/10 p-10 rounded-[2.5rem] backdrop-blur-xl shadow-2xl relative">
                    
                    <NavLink to="/" className="flex items-center gap-3">
                        <BarChart3 className="w-10 h-10 text-primary" />
                        <h1 className="text-2xl font-bold">TrendAI</h1>
                    </NavLink>

                    <div className="text-center">
                        <h2 className="text-3xl font-bold mb-2">
                            {step === 1 ? "Reset Password" : "Check Your Email"}
                        </h2>
                        <p className="text-[var(--text-secondary)]">
                            {step === 1 
                                ? "Enter your email to receive a 6-digit verification code" 
                                : `Enter the code sent to ${email}`}
                        </p>
                    </div>

                    {message.text && (
                        <div className={`w-full p-3 rounded-xl text-sm text-center flex items-center justify-center gap-2 ${
                            message.type === 'success' ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-red-500/10 text-red-500 border border-red-500/20'
                        }`}>
                            {message.type === 'success' && <CheckCircle2 className="w-4 h-4" />}
                            {message.text}
                        </div>
                    )}

                    <AnimatePresence mode="wait">
                        {step === 1 ? (
                            <motion.form 
                                key="step1" 
                                initial={{ opacity: 0, x: -20 }} 
                                animate={{ opacity: 1, x: 0 }} 
                                exit={{ opacity: 0, x: 20 }}
                                className="w-full flex flex-col gap-6" 
                                onSubmit={handleRequestOTP}
                            >
                                <div className="relative group">
                                    <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--text-secondary)]" />
                                    <input
                                        type="email"
                                        placeholder="Enter your email"
                                        required
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        className="w-full bg-white/5 border border-white/10 rounded-2xl py-4 pl-12 pr-4 outline-none focus:border-primary/50 text-lg transition-all"
                                    />
                                </div>
                                <button type="submit" disabled={loading} className="bg-primary text-white py-4 rounded-2xl font-bold flex justify-center items-center gap-2 hover:brightness-110 disabled:opacity-50">
                                    {loading ? "Sending..." : "Send Code"} <ArrowRight className="w-5 h-5" />
                                </button>
                            </motion.form>
                        ) : (
                            <motion.form 
                                key="step2" 
                                initial={{ opacity: 0, x: 20 }} 
                                animate={{ opacity: 1, x: 0 }} 
                                exit={{ opacity: 0, x: -20 }}
                                className="w-full flex flex-col gap-6" 
                                onSubmit={handleResetPassword}
                            >
                                <div className="flex flex-col gap-4">
                                    <div className="relative group">
                                        <ShieldCheck className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-primary" />
                                        <input
                                            type="text"
                                            maxLength="6"
                                            placeholder="6-digit OTP"
                                            required
                                            value={otp}
                                            onChange={(e) => setOtp(e.target.value)}
                                            className="w-full bg-white/5 border border-white/10 rounded-2xl py-4 pl-12 text-center text-xl tracking-[0.3em] font-bold outline-none focus:border-primary"
                                        />
                                    </div>
                                    <div className="relative group">
                                        <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--text-secondary)]" />
                                        <input
                                            type="password"
                                            placeholder="New Password"
                                            required
                                            value={newPassword}
                                            onChange={(e) => setNewPassword(e.target.value)}
                                            className="w-full bg-white/5 border border-white/10 rounded-2xl py-4 pl-12 pr-4 outline-none focus:border-primary/50 text-lg"
                                        />
                                    </div>
                                </div>
                                <button type="submit" disabled={loading} className="bg-primary text-white py-4 rounded-2xl font-bold flex justify-center items-center gap-2 hover:brightness-110">
                                    {loading ? "Resetting..." : "Reset Password"} <ArrowRight className="w-5 h-5" />
                                </button>
                                <button type="button" onClick={() => setStep(1)} className="text-sm text-[var(--text-secondary)] hover:text-primary transition-colors text-center">
                                    Resend Code
                                </button>
                            </motion.form>
                        )}
                    </AnimatePresence>

                    <div className="mt-4">
                        <NavLink to="/login" className="text-primary font-bold hover:underline flex items-center gap-2">
                             Back to Login
                        </NavLink>
                    </div>
                </div>
            </motion.div>
        </div>
    );
};

>>>>>>> 4463506 (Integrated TrendBot with Groq and polished UI styling)
export default ForgotPassword;