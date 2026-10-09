import React , { useState } from 'react';
import { motion } from 'framer-motion';
import { BarChart3, Mail, Lock, User, ArrowRight, Check } from 'lucide-react';
import { NavLink, useNavigate } from 'react-router-dom';
import ThemeToggle from '../components/ThemeToggle';

const Signup = () => {
    const navigate = useNavigate();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [firstName, setFirstName] = useState("");
    const [lastName, setLastName] = useState("");
    const [loading, setLoading] = useState(false);

    const handleSignup = async (e) => {
        e.preventDefault();
        setLoading(true);

        try {
            // Register the user
            const registerResponse = await fetch("/api/auth/register", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({                  
                    firstname: firstName,
                    lastname: lastName,
                    email,
                    password
                })
            });

            const registerData = await registerResponse.json();

            if (!registerResponse.ok) {
                console.error("Registration failed:", registerData.detail);
                setLoading(false);
                return;
            }

            // Automatically log in after successful registration
            const loginResponse = await fetch("/api/auth/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    email,
                    password
                })
            });

            const loginData = await loginResponse.json();

            if (loginResponse.ok) {
                // Save JWT token and navigate to dashboard
                localStorage.setItem("token", loginData.access_token);
                localStorage.setItem("is_admin", String(Boolean(loginData.is_admin)));
                navigate("/dashboard");
            } else {
                // If auto-login fails, redirect to login page
                navigate("/login");
            }

        } catch (error) {
            console.error("Signup error:", error);
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] flex items-center justify-center p-6 relative overflow-hidden">
            {/* Background gradients */}
            <div className="absolute top-0 left-0 w-[500px] h-[500px] bg-primary/10 rounded-full blur-[120px] dark:opacity-30 light:opacity-20"></div>
            <div className="absolute bottom-0 right-0 w-[400px] h-[400px] bg-secondary/10 rounded-full blur-[100px] dark:opacity-20 light:opacity-15"></div>
            
            {/* Theme Toggle - Absolute positioned */}
            <div className="absolute top-6 right-6 z-50">
                <ThemeToggle />
            </div>

            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="w-full max-w-2xl grid grid-cols-1 lg:grid-cols-2 bg-white/[0.03] dark:bg-white/[0.03] light:bg-white/80 border border-white/10 dark:border-white/10 light:border-slate-200 rounded-[3rem] overflow-hidden backdrop-blur-xl shadow-2xl shadow-primary/5 relative z-10"
            >
                {/* Left Side: Info */}
                <div className="hidden lg:flex flex-col justify-between p-12 bg-gradient-to-br from-primary/10 to-transparent border-r border-white/10 dark:border-white/10 light:border-slate-200">
                    <NavLink to="/" className="flex items-center gap-3">
                        <div className="text-primary"><BarChart3 className="w-8 h-8" /></div>
                        <h2 className="text-xl font-bold tracking-tight text-[var(--text-primary)]">TrendAI</h2>
                    </NavLink>

                    <div className="flex flex-col gap-8">
                        <h3 className="text-4xl font-black leading-tight text-[var(--text-primary)]">Start predicting with precision today.</h3>
                        <ul className="flex flex-col gap-4">
                            {[
                                "Unlimited market tracking",
                                "Real-time sentiment heatmaps",
                                "Priority AI processing",
                                "Advanced data exporting"
                            ].map((text, i) => (
                                <li key={i} className="flex items-center gap-3 text-[var(--text-secondary)]">
                                    <div className="bg-primary/20 p-1 rounded-full"><Check className="w-4 h-4 text-primary" /></div>
                                    {text}
                                </li>
                            ))}
                        </ul>
                    </div>

                    <div className="flex items-center gap-4 p-4 bg-white/5 dark:bg-white/5 light:bg-slate-100 rounded-2xl border border-white/10 dark:border-white/10 light:border-slate-200">
                        <div className="w-10 h-10 rounded-full bg-slate-800 dark:bg-slate-800 light:bg-slate-300 border border-white/10 overflow-hidden">
                            <img src="https://i.pravatar.cc/150?u=42" alt="Avatar" />
                        </div>
                        <div>
                            <p className="text-xs font-bold text-[var(--text-primary)]">"Best market tool I've used in years."</p>
                            <p className="text-[10px] text-[var(--text-secondary)]">Alex Reid, CMO at Bloom</p>
                        </div>
                    </div>
                </div>

                {/* Right Side: Form */}
                <div className="p-10 lg:p-12 flex flex-col gap-8">
                    <div className="text-center lg:text-left">
                        <h2 className="text-3xl font-bold mb-2 text-[var(--text-primary)]">Create Account</h2>
                        <p className="text-[var(--text-secondary)]">Join 5,000+ traders using TrendAI</p>
                    </div>

                    <form className="flex flex-col gap-5" onSubmit={handleSignup}>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="flex flex-col gap-2">
                                <label className="text-xs font-bold text-[var(--text-secondary)] ml-1 uppercase tracking-wider">First Name</label>
                                <input
                                    type="text"
                                    placeholder="John"
                                    value={firstName}
                                    onChange={(e) => setFirstName(e.target.value)}
                                    required
                                    className="w-full bg-white/[0.05] dark:bg-white/[0.05] light:bg-slate-50 border border-white/10 dark:border-white/10 light:border-slate-300 rounded-xl py-3 px-4 outline-none focus:border-primary/50 transition-all text-[var(--text-primary)] placeholder:text-[var(--text-secondary)]"
                                />
                            </div>
                            <div className="flex flex-col gap-2">
                                <label className="text-xs font-bold text-[var(--text-secondary)] ml-1 uppercase tracking-wider">Last Name</label>
                                <input
                                    type="text"
                                    placeholder="Doe"
                                    value={lastName}
                                    onChange={(e) => setLastName(e.target.value)}
                                    required
                                    className="w-full bg-white/[0.05] dark:bg-white/[0.05] light:bg-slate-50 border border-white/10 dark:border-white/10 light:border-slate-300 rounded-xl py-3 px-4 outline-none focus:border-primary/50 transition-all text-[var(--text-primary)] placeholder:text-[var(--text-secondary)]"
                                />
                            </div>
                        </div>

                        <div className="flex flex-col gap-2">
                            <label className="text-xs font-bold text-[var(--text-secondary)] ml-1 uppercase tracking-wider">Work Email</label>
                            <div className="relative group">
                                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-secondary)] group-focus-within:text-primary transition-colors" />
                                <input
                                    type="email"
                                    placeholder="john@company.com"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                    className="w-full bg-white/[0.05] dark:bg-white/[0.05] light:bg-slate-50 border border-white/10 dark:border-white/10 light:border-slate-300 rounded-xl py-3 pl-11 pr-4 outline-none focus:border-primary/50 transition-all text-[var(--text-primary)] placeholder:text-[var(--text-secondary)]"
                                />
                            </div>
                        </div>

                        <div className="flex flex-col gap-2">
                            <label className="text-xs font-bold text-[var(--text-secondary)] ml-1 uppercase tracking-wider">Password</label>
                            <div className="relative group">
                                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-secondary)] group-focus-within:text-primary transition-colors" />
                                <input
                                    type="password"
                                    placeholder="Min. 8 characters"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                    minLength={8}
                                    className="w-full bg-white/[0.05] dark:bg-white/[0.05] light:bg-slate-50 border border-white/10 dark:border-white/10 light:border-slate-300 rounded-xl py-3 pl-11 pr-4 outline-none focus:border-primary/50 transition-all text-[var(--text-primary)] placeholder:text-[var(--text-secondary)]"
                                />
                            </div>
                        </div>

                        <button 
                            type="submit" 
                            disabled={loading}
                            className="bg-primary text-white py-4 rounded-xl font-bold text-lg hover:brightness-110 shadow-lg shadow-primary/20 transition-all flex items-center justify-center gap-2 mt-2 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loading ? "Creating Account..." : "Create Account"} <ArrowRight className="w-5 h-5" />
                        </button>
                    </form>

                    <p className="text-[var(--text-secondary)] text-sm text-center">
                        Already have an account? <NavLink to="/login" className="text-primary font-bold hover:underline">Log in</NavLink>
                    </p>

                    <p className="text-[10px] text-[var(--text-secondary)] text-center uppercase tracking-tight">
                        By signing up, you agree to our Terms of Service & Privacy Policy.
                    </p>
                </div>
            </motion.div>
        </div>
    );
};

export default Signup;
