// import React,{useState} from 'react';
// import { motion } from 'framer-motion';
// import { Search, Rocket, Zap, CreditCard, Terminal, HelpCircle, ChevronRight, MessageSquare, Ticket, Globe } from 'lucide-react';
// import DashboardLayout from '../components/DashboardLayout';

// const HelpCenter = () => {
//     const topics = [
//         { title: 'Getting Started', desc: 'New here? Start with the basic concepts and quick setup guide.', icon: Rocket },
//         { title: 'Using AI Insights', desc: 'Master our predictive analytics and data visualization tools.', icon: Zap },
//         { title: 'Account & Billing', desc: 'Manage your subscriptions, usage limits, and invoices.', icon: CreditCard },
//         { title: 'API Docs', desc: 'Technical integration guides for TrendAI REST APIs and SDKs.', icon: Terminal },
//     ];

//     const faqs = [
//         { q: 'How do I connect my data source?', a: "Navigate to 'Settings' > 'Data Connections' and click 'Add Source'. We support AWS S3, Google BigQuery, Snowflake, and local CSV uploads." },
//         { q: 'What is the data retention policy?', a: "Standard plans retain data for 12 months. Enterprise plans offer custom retention periods up to 7 years." },
//         { q: 'Can I share reports with external users?', a: "Yes, you can generate public share links or invite guest viewers via email with restricted permissions." },
//     ];
//     const [searchQuery, setSearchQuery] = useState("");

//     const filteredFaqs = faqs.filter(faq => 
//         faq.q.toLowerCase().includes(searchQuery.toLowerCase()) ||
//         faq.a.toLowerCase().includes(searchQuery.toLowerCase())
//     );
//     const filteredTopics = topics.filter(topic =>
//         topic.title.toLowerCase().includes(searchQuery.toLowerCase())
//     );
//     const [activeFaq, setActiveFaq] = useState(null);
//     return (
//         <DashboardLayout title="Help Center">
//             <div className="max-w-6xl mx-auto space-y-20 pb-20">
//                 {/* Hero */}
//                 <section className="relative min-h-[500px] flex flex-col items-center justify-center p-12 rounded-[4rem] overflow-hidden border border-white/10 group">
//                     <div className="absolute inset-0 bg-gradient-to-br from-primary/20 via-background-dark to-background-dark transition-transform duration-1000 group-hover:scale-105"></div>
//                     <div className="absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-primary/50 to-transparent"></div>

//                     <Globe className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] text-primary/[0.03] animate-[spin_60s_linear_infinite]" />

//                     <div className="relative z-10 text-center space-y-6 max-w-3xl">
//                         <motion.h1
//                             initial={{ opacity: 0, y: 20 }}
//                             animate={{ opacity: 1, y: 0 }}
//                             className="text-6xl font-black text-white tracking-tight leading-tight"
//                         >
//                             How can we <span className="text-primary italic">help</span> you?
//                         </motion.h1>
//                         <p className="text-slate-400 text-xl font-medium">Search our documentation or browse topics below</p>

//                         <div className="pt-8 relative group/search">
//                             <div className="absolute -inset-1 bg-gradient-to-r from-primary/50 to-violet-500/50 rounded-3xl blur opacity-20 group-hover/search:opacity-40 transition duration-1000"></div>
//                             <div className="relative flex w-full h-20 bg-background-dark border border-white/20 rounded-2xl overflow-hidden focus-within:border-primary/50 transition-all">
//                                 <div className="flex items-center px-6">
//                                     <Search className="w-6 h-6 text-slate-500" />
//                                 </div>
//                                 <input
//                                     className="flex-1 bg-transparent border-none outline-none text-white text-lg placeholder:text-slate-600 px-4"
//                                     placeholder="Search for articles, guides, and more..."
//                                     value={searchQuery}
//                                     onChange={(e) => setSearchQuery(e.target.value)}
//                                 />
//                                 <div className="flex items-center px-4">
//                                     <button className="px-10 py-4 bg-primary text-background-dark font-black rounded-xl hover:scale-105 transition-all shadow-xl shadow-primary/20">
//                                         Search
//                                     </button>
//                                 </div>
//                             </div>
//                         </div>
//                     </div>
//                 </section>

//                 {/* Topics */}
//                 <section className="space-y-10">
//                     <h2 className="text-3xl font-black text-white tracking-tight">Support <span className="text-primary">Topics</span></h2>
//                     <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
//                         {filteredTopics.map((topic, i) => (
//                             <motion.div
//                                 key={topic.title}
//                                 initial={{ opacity: 0, y: 20 }}
//                                 animate={{ opacity: 1, y: 0 }}
//                                 transition={{ delay: i * 0.1 }}
//                                 className="group p-8 rounded-[2.5rem] bg-white/[0.03] border border-white/10 hover:border-primary/50 transition-all cursor-pointer relative overflow-hidden"
//                             >
//                                 <div className="absolute top-0 right-0 w-24 h-24 bg-primary/5 blur-3xl rounded-full translate-x-12 -translate-y-12"></div>
//                                 <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center text-primary mb-8 group-hover:scale-110 transition-transform duration-500">
//                                     <topic.icon className="w-8 h-8" />
//                                 </div>
//                                 <h3 className="text-xl font-black text-white mb-3">{topic.title}</h3>
//                                 <p className="text-slate-500 text-sm leading-relaxed">{topic.desc}</p>
//                             </motion.div>
//                         ))}
//                     </div>
//                 </section>

//                 {/* FAQ & Support */}
//                 <div className="grid grid-cols-1 lg:grid-cols-3 gap-16">
//                     <div className="lg:col-span-2 space-y-10">
//                         <h2 className="text-3xl font-black text-white tracking-tight">Frequently Asked Questions</h2>
//                         <div className="space-y-6">
//                             {filteredFaqs.length > 0 ? (
//                                 filteredFaqs.map((faq, i) => (
//                                     <div key={i} className="group rounded-3xl border border-white/10 bg-white/[0.02] hover:border-primary/30 transition-all overflow-hidden">
//                                         <button className="w-full flex items-center justify-between p-8 text-left" onClick={() => setActiveFaq(activeFaq === i ? null : i)}>
//                                             <span className="font-bold text-lg text-slate-200 group-hover:text-primary transition-colors">{faq.q}</span>
//                                             <ChevronRight className="w-5 h-5 text-slate-500 group-hover:translate-x-1 transition-transform" />
//                                         </button>
//                                         {activeFaq === i && (
//                                         <motion.div initial={{ height: 0 }} animate={{ height: 'auto' }}>
//                                             <div className="px-8 pb-8 text-slate-500 leading-relaxed border-t border-white/5 pt-8">
//                                                 {faq.a}
//                                             </div> 
//                                         </motion.div>
//                                         )}
//                                         {/* {i === 0 && (
//                                             <div className="px-8 pb-8 text-slate-500 leading-relaxed border-t border-white/5 pt-8">
//                                                 {faq.a}
//                                             </div>
//                                         )} */}
//                                     </div>
//                                 ))
//                                 )
//                             }
//                         </div>
//                     </div>

//                     <div className="space-y-8">
//                         <div className="p-10 rounded-[3rem] bg-gradient-to-br from-primary/10 to-transparent border border-white/10 relative overflow-hidden group">
//                             <div className="absolute -top-10 -right-10 w-40 h-40 bg-primary/10 blur-[80px] rounded-full"></div>
//                             <div className="relative z-10 space-y-8">
//                                 <div>
//                                     <h3 className="text-2xl font-black text-white">Still need help?</h3>
//                                     <p className="text-slate-500 mt-2 leading-relaxed">Our support team is available 24/7 to assist you with any technical issues.</p>
//                                 </div>
//                                 <div className="space-y-4">
//                                     <button className="w-full h-16 bg-primary text-background-dark font-black rounded-2xl flex items-center justify-center gap-3 hover:scale-[1.02] transition-all shadow-xl shadow-primary/20">
//                                         <MessageSquare className="w-5 h-5" /> Start Live Chat
//                                     </button>
//                                     <button className="w-full h-16 bg-white/5 border border-white/10 text-white font-black rounded-2xl flex items-center justify-center gap-3 hover:bg-white/10 transition-all">
//                                         <Ticket className="w-5 h-5" /> Open a Ticket
//                                     </button>
//                                 </div>
//                                 <div className="flex items-center gap-4 pt-6 border-t border-white/5">
//                                     <div className="flex -space-x-3">
//                                         {[1, 2, 3].map(i => (
//                                             <div key={i} className="w-10 h-10 rounded-full border-2 border-background-dark bg-slate-800 overflow-hidden">
//                                                 <img src={`https://i.pravatar.cc/100?u=${i}`} alt="Agent" />
//                                             </div>
//                                         ))}
//                                     </div>
//                                     <span className="text-xs font-black text-primary uppercase tracking-widest">Avg. reply: 5m</span>
//                                 </div>
//                             </div>
//                         </div>
//                     </div>
//                 </div>
//             </div>
//         </DashboardLayout>
//     );
// };

// export default HelpCenter;
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
    Search, Rocket, Zap, CreditCard, Terminal, 
    ChevronRight, MessageSquare, Ticket, Globe, X 
} from 'lucide-react';
import Chatbot from 'react-chatbot-kit';
import config from '../lib/chatbot/config';
import MessageParser from '../lib/chatbot/MessageParser';
import ActionProvider from '../lib/chatbot/ActionProvider';
import DashboardLayout from '../components/DashboardLayout';

// Optional: Import your chatbot components here if ready
// import Chatbot from 'react-chatbot-kit';
// import config from './chatbot/config';

const HelpCenter = () => {
    // 1. Data Definitions
    const topics = [
        { title: 'Getting Started', desc: 'New here? Start with the basic concepts and quick setup guide.', icon: Rocket },
        { title: 'Using AI Insights', desc: 'Master our predictive analytics and data visualization tools.', icon: Zap },
        { title: 'Account & Billing', desc: 'Manage your subscriptions, usage limits, and invoices.', icon: CreditCard },
        { title: 'API Docs', desc: 'Technical integration guides for TrendAI REST APIs and SDKs.', icon: Terminal },
    ];

    const faqs = [
        { q: 'How do I connect my data source?', a: "Navigate to 'Settings' > 'Data Connections' and click 'Add Source'. We support AWS S3, Google BigQuery, Snowflake, and local CSV uploads." },
        { q: 'What is the data retention policy?', a: "Standard plans retain data for 12 months. Enterprise plans offer custom retention periods up to 7 years." },
        { q: 'Can I share reports with external users?', a: "Yes, you can generate public share links or invite guest viewers via email with restricted permissions." },
    ];

    // 2. State Management
    const [searchQuery, setSearchQuery] = useState("");
    const [activeFaq, setActiveFaq] = useState(null); // Stores the question string
    const [isChatOpen, setIsChatOpen] = useState(false);

    // 3. Filtering Logic
    const filteredFaqs = faqs.filter(faq => 
        faq.q.toLowerCase().includes(searchQuery.toLowerCase()) ||
        faq.a.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const filteredTopics = topics.filter(topic =>
        topic.title.toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
        <DashboardLayout title="Help Center">
            <div className="max-w-6xl mx-auto space-y-20 pb-20 px-4">
                
                {/* Hero Section */}
                <section className="relative min-h-[500px] flex flex-col items-center justify-center p-6 md:p-12 rounded-[3rem] md:rounded-[4rem] overflow-hidden border border-white/10 group">
                    <div className="absolute inset-0 bg-gradient-to-br from-primary/20 via-background-dark to-background-dark transition-transform duration-1000 group-hover:scale-105"></div>
                    <div className="absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-primary/50 to-transparent"></div>
                    <Globe className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] text-primary/[0.03] animate-[spin_60s_linear_infinite]" />

                    <div className="relative z-10 text-center space-y-6 max-w-3xl">
                        <motion.h1
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="text-4xl md:text-6xl font-black text-white tracking-tight leading-tight"
                        >
                            How can we <span className="text-primary italic">help</span> you?
                        </motion.h1>
                        <p className="text-slate-400 text-lg md:text-xl font-medium">Search our documentation or browse topics below</p>

                        <div className="pt-8 relative group/search max-w-2xl mx-auto w-full">
                            <div className="absolute -inset-1 bg-gradient-to-r from-primary/50 to-violet-500/50 rounded-3xl blur opacity-20 group-hover/search:opacity-40 transition duration-1000"></div>
                            <div className="relative flex w-full h-16 md:h-20 bg-background-dark border border-white/20 rounded-2xl overflow-hidden focus-within:border-primary/50 transition-all">
                                <div className="flex items-center px-6">
                                    <Search className="w-6 h-6 text-slate-500" />
                                </div>
                                <input
                                    className="flex-1 bg-transparent border-none outline-none text-white text-lg placeholder:text-slate-600 px-4"
                                    placeholder="Search for articles..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                />
                                {searchQuery && (
                                    <button onClick={() => setSearchQuery("")} className="pr-4 text-slate-500 hover:text-white">
                                        <X className="w-5 h-5" />
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>
                </section>

                {/* Topics Section */}
                <section className="space-y-10">
                    <h2 className="text-3xl font-black text-white tracking-tight">
                        Support <span className="text-primary">Topics</span>
                    </h2>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
                        {filteredTopics.length > 0 ? (
                            filteredTopics.map((topic, i) => (
                                <motion.div
                                    key={topic.title}
                                    initial={{ opacity: 0, y: 20 }}
                                    whileInView={{ opacity: 1, y: 0 }}
                                    viewport={{ once: true }}
                                    transition={{ delay: i * 0.1 }}
                                    className="group p-8 rounded-[2.5rem] bg-white/[0.03] border border-white/10 hover:border-primary/50 transition-all cursor-pointer relative overflow-hidden"
                                >
                                    <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center text-primary mb-8 group-hover:scale-110 transition-transform duration-500">
                                        <topic.icon className="w-8 h-8" />
                                    </div>
                                    <h3 className="text-xl font-black text-white mb-3">{topic.title}</h3>
                                    <p className="text-slate-500 text-sm leading-relaxed">{topic.desc}</p>
                                </motion.div>
                            ))
                        ) : (
                            <p className="text-slate-500 italic">No topics match your search.</p>
                        )}
                    </div>
                </section>

                {/* FAQ & Support Section */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-16">
                    <div className="lg:col-span-2 space-y-10">
                        <h2 className="text-3xl font-black text-white tracking-tight">Frequently Asked Questions</h2>
                        <div className="space-y-6">
                            {filteredFaqs.length > 0 ? (
                                filteredFaqs.map((faq) => (
                                    <div key={faq.q} className="group rounded-3xl border border-white/10 bg-white/[0.02] hover:border-primary/30 transition-all overflow-hidden">
                                        <button 
                                            className="w-full flex items-center justify-between p-8 text-left" 
                                            onClick={() => setActiveFaq(activeFaq === faq.q ? null : faq.q)}
                                        >
                                            <span className={`font-bold text-lg transition-colors ${activeFaq === faq.q ? 'text-primary' : 'text-slate-200 group-hover:text-primary'}`}>
                                                {faq.q}
                                            </span>
                                            <ChevronRight className={`w-5 h-5 text-slate-500 transition-transform ${activeFaq === faq.q ? 'rotate-90 text-primary' : ''}`} />
                                        </button>
                                        
                                        <AnimatePresence>
                                            {activeFaq === faq.q && (
                                                <motion.div 
                                                    initial={{ height: 0, opacity: 0 }} 
                                                    animate={{ height: 'auto', opacity: 1 }}
                                                    exit={{ height: 0, opacity: 0 }}
                                                    transition={{ duration: 0.3 }}
                                                >
                                                    <div className="px-8 pb-8 text-slate-400 leading-relaxed border-t border-white/5 pt-8">
                                                        {faq.a}
                                                    </div> 
                                                </motion.div>
                                            )}
                                        </AnimatePresence>
                                    </div>
                                ))
                            ) : (
                                <div className="p-10 border border-dashed border-white/10 rounded-3xl text-center">
                                    <p className="text-slate-500">No FAQs found matching your criteria.</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Support Sidebar */}
                    <div className="space-y-8">
                        <div className="p-10 rounded-[3rem] bg-gradient-to-br from-primary/10 to-transparent border border-white/10 relative overflow-hidden">
                            <div className="relative z-10 space-y-8">
                                <div>
                                    <h3 className="text-2xl font-black text-white">Still need help?</h3>
                                    <p className="text-slate-500 mt-2 leading-relaxed">Our support team is available 24/7.</p>
                                </div>
                                <div className="space-y-4">
                                    <button 
                                        onClick={() => setIsChatOpen(true)}
                                        className="w-full h-16 bg-primary text-background-dark font-black rounded-2xl flex items-center justify-center gap-3 hover:scale-[1.02] transition-all shadow-xl shadow-primary/20"
                                    >
                                        <MessageSquare className="w-5 h-5" /> Start Live Chat
                                    </button>
                                    <button className="w-full h-16 bg-white/5 border border-white/10 text-white font-black rounded-2xl flex items-center justify-center gap-3 hover:bg-white/10 transition-all">
                                        <Ticket className="w-5 h-5" /> Open a Ticket
                                    </button>
                                </div>
                                <div className="flex items-center gap-4 pt-6 border-t border-white/5">
                                    <div className="flex -space-x-3">
                                        {[1, 2, 3].map(i => (
                                            <div key={i} className="w-10 h-10 rounded-full border-2 border-background-dark bg-slate-800 overflow-hidden">
                                                <img src={`https://i.pravatar.cc/100?u=${i}`} alt="Agent" />
                                            </div>
                                        ))}
                                    </div>
                                    <span className="text-xs font-black text-primary uppercase tracking-widest">Avg. reply: 5m</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Floating Chatbot Integration Point */}
            {/* {isChatOpen && (
                <div className="fixed bottom-6 right-6 z-[100] w-[350px] h-[500px] bg-background-dark border border-white/10 rounded-3xl shadow-2xl flex flex-col">
                    <div className="p-4 border-b border-white/10 flex justify-between items-center bg-white/5">
                        <span className="font-bold text-white">TrendBot Support</span>
                        <button onClick={() => setIsChatOpen(false)} className="text-slate-400 hover:text-white">
                            <X className="w-5 h-5" />
                        </button>
                    </div>
                    <div className="flex-1 overflow-hidden">
                        <Chatbot
                            config={config}
                            messageParser={MessageParser}
                            actionProvider={ActionProvider}
                        />
                        <div className="p-8 text-center text-slate-500 h-full flex flex-col justify-center">
                            <p>Chatbot UI goes here.</p>
                            <p className="text-xs mt-2">Connect your React-Chatbot-Kit component.</p>
                        </div>
                    </div>
                </div>
            )} */}
            {/* Floating Chatbot Integration Point */}
            {isChatOpen && (
                <div className="fixed bottom-6 right-6 z-[100] w-[375px] max-h-[600px] h-[80vh] bg-background-dark border border-white/10 rounded-3xl shadow-2xl flex flex-col overflow-hidden animate-in slide-in-from-bottom-5">
                    
                    {/* Header - Stays fixed at the top of the chat window */}
                    <div className="p-4 border-b border-white/10 flex justify-between items-center bg-white/5 backdrop-blur-md">
                        <div className="flex items-center gap-3">
                            <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                            <span className="font-bold text-white text-sm tracking-tight">TrendAI Assistant</span>
                        </div>
                        <button 
                            onClick={() => setIsChatOpen(false)} 
                            className="p-1 hover:bg-white/10 rounded-lg transition-colors text-slate-400 hover:text-white"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    </div>

                    {/* The Actual Chatbot Wrapper */}
                    <div className="flex-1 overflow-y-auto chatbot-container">
                        <Chatbot
                            config={config}
                            messageParser={MessageParser}
                            actionProvider={ActionProvider}
                        />
                    </div>
                </div>
            )}
        </DashboardLayout>
    );
};

export default HelpCenter;