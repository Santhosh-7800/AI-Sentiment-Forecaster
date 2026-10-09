import React from 'react';
import { motion } from 'framer-motion';
import { BarChart3, Download, Cpu, LineChart, Smile, TrendingUp, Package, ArrowUpRight, CheckCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import Layout from '../components/Layout';

const Landing = () => {
    return (
        <Layout>
            {/* Hero Section */}
            <section className="px-6 lg:px-20 py-20 lg:py-32 max-w-7xl mx-auto overflow-hidden">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
                    <motion.div
                        initial={{ opacity: 0, x: -50 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.8 }}
                        className="flex flex-col gap-8 text-center lg:text-left"
                    >
                        <div className="flex flex-col gap-4">
                            <span className="text-primary text-sm font-bold tracking-widest uppercase">Next-Gen Market Intelligence</span>
                            <h1 className="text-5xl lg:text-7xl font-black leading-tight tracking-tight text-[var(--text-primary)]">
                                Predict the <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-blue-400">Future</span> of Markets with AI
                            </h1>
                            <p className="text-lg text-[var(--text-secondary)] max-w-lg mx-auto lg:mx-0 leading-relaxed">
                                TrendAI leverages advanced machine learning to analyze consumer sentiment and forecast market shifts in real-time. Stay two steps ahead of your competition.
                            </p>
                        </div>
                        <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
                            <Link to="/signup">
                                <button className="bg-primary text-white rounded-xl px-10 py-5 text-lg font-bold hover:scale-105 transition-all shadow-[0_0_30px_rgba(13,204,242,0.4)]">
                                    Start Free Analysis
                                </button>
                            </Link>
                            <Link to="/login">
                                <button className="border border-white/10 dark:border-white/10 light:border-slate-300 bg-white/5 dark:bg-white/5 light:bg-slate-100 backdrop-blur-sm rounded-xl px-10 py-5 text-lg font-bold hover:bg-white/10 dark:hover:bg-white/10 light:hover:bg-slate-200 transition-all flex items-center justify-center gap-2 text-[var(--text-primary)]">
                                    View Demo <ArrowUpRight className="w-5 h-5" />
                                </button>
                            </Link>
                        </div>
                    </motion.div>

                    <motion.div
                        initial={{ opacity: 0, scale: 0.8 }}
                        whileInView={{ opacity: 1, scale: 1 }}
                        viewport={{ once: true }}
                        transition={{ duration: 1 }}
                        className="relative group"
                    >
                        <div className="absolute -inset-1 bg-gradient-to-r from-primary to-blue-600 rounded-3xl blur opacity-20 group-hover:opacity-40 transition duration-1000"></div>
                        <div className="relative aspect-video rounded-3xl bg-slate-900 dark:bg-slate-900 light:bg-slate-200 border border-white/10 dark:border-white/10 light:border-slate-300 overflow-hidden shadow-2xl">
                            <div
                                className="w-full h-full bg-cover bg-center"
                                style={{ backgroundImage: "url('https://lh3.googleusercontent.com/aida-public/AB6AXuB5DolK7-rAGvA48KTD2GXhgcIJ--O92jImFts-Tjdo7GpivxCyoqBUrruJanIlLMK0-rhRo8e-ix0WLkFpja446wdZBixnp2MMz_-Cpaylc0hsGenpcs81DckdhDhRWq1Zhhc47G6ipKOPYODpgOkAa5SF-V-iRXlervq_Q4qwkCRwJs_cBUNyR1T7Yp7c2FoWzV1C4dXXoJgDfwFfyrCTOiKC3bdVDljNPfQ97y1UGRXH3wWBobtfzkZ7Rqfu5OLYddnqsG_pttVo')" }}
                            />
                        </div>
                    </motion.div>
                </div>
            </section>

            {/* Methodology Section */}
            <section className="bg-white/[0.02] dark:bg-white/[0.02] light:bg-slate-50 py-32 px-6 lg:px-20 border-y border-white/5 dark:border-white/5 light:border-slate-200">
                <div className="max-w-7xl mx-auto">
                    <div className="flex flex-col gap-4 mb-20 text-center">
                        <h2 className="text-primary text-sm font-bold tracking-widest uppercase">Our Methodology</h2>
                        <h3 className="text-4xl lg:text-5xl font-bold text-[var(--text-primary)]">Real-time Data Analysis Pipeline</h3>
                        <p className="text-[var(--text-secondary)] max-w-2xl mx-auto lg:text-lg">Our platform processes millions of data points across social media, news, and e-commerce to give you a definitive competitive edge.</p>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
                        {[
                            { icon: Download, title: "Data Collection", desc: "We aggregate global data from diverse digital sources instantly, including social feeds, news outlets, and market indices." },
                            { icon: Cpu, title: "AI Processing", desc: "Our proprietary LLMs and neural networks identify emerging patterns, hidden correlations, and consumer moods." },
                            { icon: LineChart, title: "Insights", desc: "Receive clear, data-backed reports and interactive dashboards to inform your product and marketing strategy." }
                        ].map((item, idx) => (
                            <motion.div
                                key={idx}
                                initial={{ opacity: 0, y: 30 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: idx * 0.2 }}
                                className="bg-white/[0.03] dark:bg-white/[0.03] light:bg-white border border-white/10 dark:border-white/10 light:border-slate-300 p-10 rounded-[2.5rem] hover:border-primary/50 transition-all group"
                            >
                                <div className="bg-primary/10 w-16 h-16 rounded-2xl flex items-center justify-center mb-8 text-primary group-hover:scale-110 group-hover:bg-primary group-hover:text-white transition-all duration-500">
                                    <item.icon className="w-8 h-8" />
                                </div>
                                <h4 className="text-2xl font-bold mb-4 text-[var(--text-primary)]">{item.title}</h4>
                                <p className="text-[var(--text-secondary)] text-lg leading-relaxed">{item.desc}</p>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Features Section */}
            <section className="py-32 px-6 lg:px-20 max-w-7xl mx-auto">
                <div className="text-center mb-24">
                    <h2 className="text-4xl lg:text-5xl font-bold mb-6 text-[var(--text-primary)]">Powerful Features for Growth</h2>
                    <div className="h-1.5 w-24 bg-gradient-to-r from-primary to-blue-500 mx-auto rounded-full"></div>
                </div>

                <div className="flex flex-col gap-40">
                    {[
                        {
                            title: "Sentiment Analysis",
                            subtitle: "Consumer Intelligence",
                            icon: Smile,
                            desc: "Understand the 'Why' behind market movements. Our NLP engine deciphers public emotion across millions of conversations to gauge true consumer sentiment.",
                            bullets: ["Emotion-weighted scoring", "Real-time brand health monitoring"],
                            image: "https://lh3.googleusercontent.com/aida-public/AB6AXuDKI631bX2_vOe5u2grwPXOgbqbiAGpQZBv9gqLZscDPAfbVmYe6yVlwr8gXrCpkiwlAHAGS75WZ91uP0PxC-_mrWwKtVC4pT7W-w70AGfx8y3JmTXjBpY5BmK-cHCxkTVWw8XeSGWcAZMhMZqh3CoqD4av6Z9md3sqOrPQ8LXgjrg1M-NbQ4k_YktDg0mVa3I2L_ZEwzTwXKE4IBROhYXXAU2jnw1tm1kAHdEg5OZaNoocO3CiPV90-u5PrNHR_bZspwDA0oHgyBmk",
                            reverse: false
                        },
                        {
                            title: "Trend Forecasting",
                            subtitle: "Predictive Power",
                            icon: TrendingUp,
                            desc: "Identify tomorrow's hits today. Our algorithms detect early signals of emerging trends before they go mainstream, allowing you to innovate ahead.",
                            bullets: ["30-day predictive windows", "Categorical trend mapping"],
                            image: "https://lh3.googleusercontent.com/aida-public/AB6AXuBIMpFR39liT6XtZirP0bYK8K3NUNEY_cUzaXdVLpUV4m0yXRVcnllqVw3LeP4Y6NxmFbLKAmjpSimM7WkQKNgSmGYxXqgzNF7YWG3hZMoJ-WOpxWTpLA47GedQMhS2nsWQX7VpTem9x3eBwv1QP81lYFJe9ZkaXW8uLyAwcmhbrhnlcy2ZBuNnUvtpFoD1FslXxK0YY9cenACj3MMtdt7IgLHEW4lky9RUDALMLhyoXr0LdWnizoHqAe1hTsRCEES1Kl66RlQYvvLf",
                            reverse: true
                        }
                    ].map((feature, idx) => (
                        <div key={idx} className={`flex flex-col lg:flex-row items-center gap-20 ${feature.reverse ? 'lg:flex-row-reverse' : ''}`}>
                            <motion.div
                                initial={{ opacity: 0, x: feature.reverse ? 50 : -50 }}
                                whileInView={{ opacity: 1, x: 0 }}
                                viewport={{ once: true }}
                                className="w-full lg:w-1/2 flex flex-col gap-8"
                            >
                                <div className="inline-flex items-center gap-2 text-primary font-bold tracking-wider uppercase text-sm">
                                    <feature.icon className="w-5 h-5" />
                                    <span>{feature.subtitle}</span>
                                </div>
                                <h3 className="text-4xl font-bold text-[var(--text-primary)]">{feature.title}</h3>
                                <p className="text-[var(--text-secondary)] text-xl leading-relaxed">{feature.desc}</p>
                                <ul className="space-y-4">
                                    {feature.bullets.map((bullet, bIdx) => (
                                        <li key={bIdx} className="flex items-center gap-4 text-[var(--text-secondary)] text-lg">
                                            <CheckCircle className="w-6 h-6 text-primary" />
                                            {bullet}
                                        </li>
                                    ))}
                                </ul>
                            </motion.div>
                            <motion.div
                                initial={{ opacity: 0, scale: 0.9 }}
                                whileInView={{ opacity: 1, scale: 1 }}
                                viewport={{ once: true }}
                                className="w-full lg:w-1/2 group relative"
                            >
                                <div className="absolute -inset-2 bg-gradient-to-r from-primary/30 to-blue-500/30 rounded-[3rem] blur-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>
                                <div className="relative aspect-4/3 rounded-[3rem] overflow-hidden border border-white/10 dark:border-white/10 light:border-slate-300 shadow-2xl">
                                    <div
                                        className="w-full h-full bg-cover bg-center group-hover:scale-110 transition-transform duration-1000"
                                        style={{ backgroundImage: `url('${feature.image}')` }}
                                    />
                                </div>
                            </motion.div>
                        </div>
                    ))}
                </div>
            </section>

            {/* CTA Section */}
            <section className="py-32 px-6 lg:px-20 max-w-6xl mx-auto">
                <motion.div
                    initial={{ opacity: 0, y: 50 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="bg-gradient-to-br from-primary/20 via-blue-500/10 to-transparent border border-white/10 dark:border-white/10 light:border-slate-300 p-16 lg:p-24 rounded-[4rem] flex flex-col items-center gap-10 text-center relative overflow-hidden group"
                >
                    <div className="absolute top-0 right-0 w-96 h-96 bg-primary/20 blur-[120px] rounded-full -mr-48 -mt-48 animate-pulse"></div>
                    <h2 className="text-4xl lg:text-6xl font-black leading-tight max-w-4xl relative z-10 text-[var(--text-primary)]">
                        Ready to see into the future of your market?
                    </h2>
                    <p className="text-[var(--text-secondary)] text-xl max-w-2xl relative z-10">
                        Join 500+ forward-thinking brands navigating market complexity with absolute confidence.
                    </p>
                    <div className="flex flex-col sm:flex-row gap-6 w-full sm:w-auto relative z-10">
                        <Link to="/signup">
                            <button className="bg-primary text-white rounded-2xl px-12 py-6 text-xl font-bold hover:brightness-110 shadow-2xl shadow-primary/30 transition-all">
                                Get Started Now
                            </button>
                        </Link>
                        <Link to="/login">
                            <button className="bg-white/5 dark:bg-white/5 light:bg-slate-100 backdrop-blur-md border border-white/10 dark:border-white/10 light:border-slate-300 rounded-2xl px-12 py-6 text-xl font-bold hover:bg-white/10 dark:hover:bg-white/10 light:hover:bg-slate-200 transition-all text-[var(--text-primary)]">
                                Contact Sales
                            </button>
                        </Link>
                    </div>
                    
                </motion.div>
            </section>
        </Layout>
    );
};

export default Landing;
