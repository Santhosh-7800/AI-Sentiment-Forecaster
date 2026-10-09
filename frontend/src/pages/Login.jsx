import React,{useState} from 'react';
import { motion,AnimatePresence } from 'framer-motion';
import { BarChart3, Mail, Lock, ArrowRight,ShieldCheck } from 'lucide-react';
import { NavLink, useNavigate } from 'react-router-dom';
import ThemeToggle from '../components/ThemeToggle';

const Login = () => {
    const navigate = useNavigate();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [otp, setOtp] = useState("");
    const [step, setStep] = useState("login"); // "login" or "2fa"
    const [error, setError] = useState("");
    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError("");
        try {
            const response = await fetch("/api/auth/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    email,
                    password
                })
            });

            const data = await response.json();

            if (!response.ok) {
                setError(data.detail || "Login failed");
                setLoading(false);
                return;
            }
            if (data.status === "2fa_required") {
                setStep("2fa");
            } else if (data.access_token) {
                localStorage.setItem("token", data.access_token);
                localStorage.setItem("is_admin", String(Boolean(data.is_admin)));
                navigate("/dashboard");
            }

        } catch (error) {
            console.error("Login error:", error);
        } finally {
            setLoading(false);
        }
    };
    const handleVerify2FA = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError("");

        try {
            const response = await fetch("/api/auth/verify-2fa", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, code: otp })
            });

            const data = await response.json();

            if (response.ok && data.access_token) {
                localStorage.setItem("token", data.access_token);
                localStorage.setItem("is_admin", String(Boolean(data.is_admin)));
                navigate("/dashboard");
            } else {
                setError(data.detail || "Invalid OTP");
            }
        } catch (err) {
            setError("Failed to verify OTP.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] flex items-center justify-center p-6 relative overflow-hidden">
            {/* Background gradients */}
            <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-primary/10 rounded-full blur-[120px] dark:opacity-30 light:opacity-20"></div>
            <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-secondary/10 rounded-full blur-[100px] dark:opacity-20 light:opacity-15"></div>
            
            {/* Theme Toggle - Absolute positioned */}
            <div className="absolute top-6 right-6 z-50">
                <ThemeToggle />
            </div>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="w-full max-w-md relative z-10"
            >
                <div className="flex flex-col items-center gap-8 bg-white/[0.03] dark:bg-white/[0.03] light:bg-white/80 border border-white/10 dark:border-white/10 light:border-slate-200 p-10 rounded-[2.5rem] backdrop-blur-xl shadow-2xl relative overflow-hidden group">
                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-primary/50 to-transparent"></div>

                    <NavLink to="/" className="flex items-center gap-3 group/logo">
                        <div className="text-primary group-hover/logo:scale-110 transition-transform">
                            <BarChart3 className="w-10 h-10" />
                        </div>
                        <h1 className="text-2xl font-bold tracking-tight text-[var(--text-primary)]">TrendAI</h1>
                    </NavLink>

                    <div className="text-center">
                        <h2 className="text-3xl font-bold mb-2 text-[var(--text-primary)]">
                            {step === "login" ? "Welcome Back" : "Security Check"}
                        </h2>
                        <p className="text-[var(--text-secondary)]">
                            {step === "login" 
                                ? "Enter your credentials to access your dashboard" 
                                : `We've sent a code to ${email}`}
                        </p>
                    </div>
                    {error && (
                        <div className="w-full bg-red-500/10 border border-red-500/20 text-red-500 p-3 rounded-xl text-sm text-center">
                            {error}
                        </div>
                    )}
                    <AnimatePresence mode="wait">
                        {step === "login" ? (
                            /* --- LOGIN FORM --- */
                            <motion.form 
                                key="login-form"
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: 20 }}
                                className="w-full flex flex-col gap-6" 
                                onSubmit={handleLogin}
                            >
                                <div className="flex flex-col gap-2">
                                    <label className="text-sm font-bold text-[var(--text-secondary)] ml-1">Email Address</label>
                                    <div className="relative group/input">
                                        <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--text-secondary)] group-focus-within/input:text-primary transition-colors" />
                                        <input
                                            type="email"
                                            placeholder="name@company.com"
                                            value={email}
                                            onChange={(e) => setEmail(e.target.value)}
                                            required
                                            className="w-full bg-white/5 border border-white/10 rounded-2xl py-4 pl-12 pr-4 outline-none focus:border-primary/50 transition-all text-lg"
                                        />
                                    </div>
                                </div>

                                <div className="flex flex-col gap-2">
                                    <div className="flex justify-between items-center ml-1">
                                        <label className="text-sm font-bold text-[var(--text-secondary)]">Password</label>
                                        <NavLink to="/forgot-password" size="sm" className="text-xs text-primary hover:underline">Forgot password?</NavLink>
                                    </div>
                                    <div className="relative group/input">
                                        <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--text-secondary)] group-focus-within/input:text-primary transition-colors" />
                                        <input
                                            type="password"
                                            placeholder="••••••••"
                                            value={password}
                                            onChange={(e) => setPassword(e.target.value)}
                                            required
                                            className="w-full bg-white/5 border border-white/10 rounded-2xl py-4 pl-12 pr-4 outline-none focus:border-primary/50 transition-all text-lg"
                                        />
                                    </div>
                                </div>

                                <button 
                                    type="submit" 
                                    disabled={loading}
                                    className="bg-primary text-white py-4 rounded-2xl font-bold text-lg hover:brightness-110 shadow-lg shadow-primary/20 transition-all flex items-center justify-center gap-2 mt-2 disabled:opacity-50"
                                >
                                    {loading ? "Signing In..." : "Sign In"} <ArrowRight className="w-5 h-5" />
                                </button>
                            </motion.form>
                        ) : (
                            /* --- 2FA OTP FORM --- */
                            <motion.form 
                                key="otp-form"
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -20 }}
                                className="w-full flex flex-col gap-6" 
                                onSubmit={handleVerify2FA}
                            >
                                <div className="flex flex-col gap-2">
                                    <label className="text-sm font-bold text-[var(--text-secondary)] text-center">Verification Code</label>
                                    <div className="relative group/input">
                                        <ShieldCheck className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-primary" />
                                        <input
                                            type="text"
                                            maxLength="6"
                                            placeholder="000000"
                                            value={otp}
                                            onChange={(e) => setOtp(e.target.value)}
                                            required
                                            className="w-full bg-white/5 border border-white/10 rounded-2xl py-4 text-center text-2xl tracking-[0.5em] font-bold outline-none focus:border-primary transition-all"
                                        />
                                    </div>
                                </div>

                                <button 
                                    type="submit" 
                                    disabled={loading}
                                    className="bg-primary text-white py-4 rounded-2xl font-bold text-lg hover:brightness-110 shadow-lg shadow-primary/20 transition-all flex items-center justify-center gap-2 mt-2 disabled:opacity-50"
                                >
                                    {loading ? "Verifying..." : "Verify & Login"} <ArrowRight className="w-5 h-5" />
                                </button>

                                <button 
                                    type="button"
                                    onClick={() => setStep("login")}
                                    className="text-sm text-[var(--text-secondary)] hover:text-primary transition-colors text-center"
                                >
                                    Back to Login
                                </button>
                            </motion.form>
                        )}
                    </AnimatePresence>
                            

                    <p className="text-[var(--text-secondary)] text-sm mt-4">
                        Don't have an account? <NavLink to="/signup" className="text-primary font-bold hover:underline">Sign up for free</NavLink>
                    </p>
                </div>
            </motion.div>
        </div>
    );
};

export default Login;
