
import React, { useState, useEffect ,useRef} from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { User, Shield, Bell, CreditCard, Camera, Mail, KeyRound, CheckCircle2 } from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';
import { apiFetch } from '../lib/api';

const Settings = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const fileInputRef = useRef(null);
    const billingRef = useRef(null);
    const [profile, setProfile] = useState({ firstname: '', lastname: '', email: '' });
    const [form, setForm] = useState({ firstname: '', lastname: '', email: '' });

    const [settings, setSettings] = useState({
        emailAlerts: true,
        systemUpdates: true,
        twoFactorEnabled: false,
        plan: 'Free',
        price: 'INR 0',
        cardLast4: '4242',
        cardExpiry: '12/26',
        usage: { ai: 0, storage: 0 }
    });

    const [passwordForm, setPasswordForm] = useState({ current: '', new: '', confirm: '' });
    const [saving, setSaving] = useState(false);
    const [checkoutLoading, setCheckoutLoading] = useState(false);
    const [message, setMessage] = useState('');
    const [paymentModal, setPaymentModal] = useState({
        open: false,
        plan: '',
        price: '',
        paymentId: ''
    });
    const autoUpgradeHandledRef = useRef(false);

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token) { navigate('/login'); return; }
        const fetchUser = async () => {
            const res = await apiFetch('/api/me');
            if (res.ok) {
                const data = await res.json();
                const userData = {
                    firstname: data.firstname || '',
                    lastname: data.lastname || '',
                    email: data.email || ''
                };
                setProfile(userData);
                setForm(userData);
        const res = await apiFetch('/api/me');
            if (res.ok) {
                const data = await res.json();
                setTopNavUser(data); // Update the top-right image here
            }
        };
        Promise.all([
            apiFetch('/api/me'),
            apiFetch('/api/settings'),
            apiFetch('/api/billing/subscription-status')  // New: Get subscription status
        ]).then(async ([profileRes, settingsRes, subStatusRes]) => {
            if (profileRes.ok) {
                const data = await profileRes.json();
                const userData = {
                    firstname: data.firstname || '',
                    lastname: data.lastname || '',
                    email: data.email || ''
                };
                setProfile(userData);
                setForm(userData);
            }
            if (settingsRes.ok) {
                const data = await settingsRes.json();
                setSettings(prev => ({ ...prev, ...data }));
            }
            // New: Process subscription status
            if (subStatusRes.ok) {
                const subStatus = await subStatusRes.json();
                console.log('[INFO] Subscription status:', subStatus);
                setSettings(prev => ({
                    ...prev,
                    subscription_status: subStatus.payment_status,
                    plan_expiry_date: subStatus.plan_expiry_date,
                    remaining_days: subStatus.remaining_days,
                    is_expired: subStatus.is_expired
                }));
            }
        }).catch(err => console.error("Fetch error:", err));
        window.addEventListener('profileUpdated', fetchUser);
        return () => window.removeEventListener('profileUpdated', fetchUser);
    }, [navigate]);

    // Scroll to billing section if coming from Sidebar
    useEffect(() => {
        if (location.state?.scrollToBilling && billingRef.current) {
            setTimeout(() => {
                billingRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 300);
        }
    }, [location]);

    const handleProfileChange = (field, value) => {
        setForm(prev => ({ ...prev, [field]: value }));
    };
    const onProfilePictureChange = (event) => {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onloadend = () => {
                // Update local preview and add to form state for saving
                setSettings(prev => ({ ...prev, profilePictureUrl: reader.result }));
                // Important: Also add file to form state so handleSave knows it needs uploading
                setForm(prev => ({ ...prev, profilePicture: file }));
            };
            reader.readAsDataURL(file);
        }
    };
    const toggleSetting = (key) => {
        setSettings(prev => ({ ...prev, [key]: !prev[key] }));
    };

    const handleSave = async () => {
        try {
            setSaving(true);
            setMessage('');

            const [profileRes] = await Promise.all([
                apiFetch('/api/me', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(form),
                }),
                apiFetch('/api/settings', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(settings),
                })
            ]);

            if (profileRes.ok) {
                const result = await profileRes.json();
                const updated = result.user || form;
                setProfile(updated);
                window.dispatchEvent(new Event('profileUpdated'));
                setMessage('Settings saved successfully');
                setTimeout(() => setMessage(''), 3000);
            }
        } catch (err) {
            setMessage('Failed to save settings');
        } finally {
            setSaving(false);
        }
    };
    const PLAN_DETAILS = {
        'Free': { price: 'INR 0', amountInr: 0, ai: 10, storage: 5 },
        'Pro Business': { price: 'INR 10000', amountInr: 1000000, ai: 80, storage: 60 },
        'Enterprise': { price: 'INR 20000', amountInr: 2000000, ai: 100, storage: 100 }
    };
    const PLAN_TAGS = {
        'Free': 'Starter',
        'Pro Business': 'Most Popular',
        'Enterprise': 'Scale',
    };

    const loadRazorpaySdk = async () => {
        if (window.Razorpay) return true;
        return new Promise((resolve) => {
            const script = document.createElement('script');
            script.src = 'https://checkout.razorpay.com/v1/checkout.js';
            script.onload = () => resolve(true);
            script.onerror = () => resolve(false);
            document.body.appendChild(script);
        });
    };

    const persistFreePlan = async (newPlan) => {
        const details = PLAN_DETAILS[newPlan];
        const nextSettings = {
            ...settings,
 }
    };
    const handlePlanChange = (newPlan) => {
        const details = PLAN_DETAILS[newPlan];
        setSettings(prev => ({
            ...prev,
            plan: newPlan,
            price: details.price,
            usage: {
                ai: details.ai,
                storage: details.storage
            }
        };
        setSettings(nextSettings);

        const res = await apiFetch('/api/settings', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(nextSettings),
        });
        if (!res.ok) {
            throw new Error('Failed to update plan settings');
        }
    };

    const startRazorpayCheckout = async (newPlan) => {
        const details = PLAN_DETAILS[newPlan];
        if (!details || details.amountInr <= 0) {
            throw new Error('Invalid paid plan selected');
        }

        const sdkLoaded = await loadRazorpaySdk();
        if (!sdkLoaded) {
            throw new Error('Failed to load Razorpay SDK');
        }

        const orderRes = await apiFetch('/api/billing/create-order', {
            skipAuthRedirect: true,
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ plan: newPlan }),
        });
        const orderData = await orderRes.json();
        if (!orderRes.ok) {
            throw new Error(orderData.detail || 'Could not create payment order');
        }

        await new Promise((resolve, reject) => {
            const razorpay = new window.Razorpay({
                key: orderData.key_id,
                amount: orderData.amount,
                currency: orderData.currency || 'INR',
                name: 'TrendAI',
                description: `${newPlan} plan upgrade`,
                order_id: orderData.order_id,
                prefill: {
                    name: `${form.firstname || ''} ${form.lastname || ''}`.trim(),
                    email: form.email || profile.email,
                },
                notes: {
                    plan: newPlan,
                },
                theme: { color: '#0DCAF2' },
                handler: async (response) => {
                    try {
                        const verifyRes = await apiFetch('/api/billing/verify', {
                            skipAuthRedirect: true,
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                plan: newPlan,
                                ...response,
                            }),
                        });
                        const verifyData = await verifyRes.json();
                        if (!verifyRes.ok) {
                            throw new Error(verifyData.detail || 'Payment verification failed');
                        }

                        if (verifyData.settings) {
                            setSettings((prev) => ({ ...prev, ...verifyData.settings }));
                        }
                        setPaymentModal({
                            open: true,
                            plan: newPlan,
                            price: PLAN_DETAILS[newPlan]?.price || '',
                            paymentId: response?.razorpay_payment_id || ''
                        });
                        setMessage(verifyData.message || `Payment successful. Account upgraded to ${newPlan}.`);
                        setTimeout(() => setMessage(''), 4000);
                        resolve(true);
                    } catch (err) {
                        reject(err);
                    }
                },
                modal: {
                    ondismiss: () => reject(new Error('Payment cancelled')),
                },
            });

            razorpay.on('payment.failed', (resp) => {
                const reason = resp?.error?.description || 'Payment failed';
                reject(new Error(reason));
            });

            razorpay.open();
        });
    };

    const handlePlanChange = async (newPlan) => {
        if (!PLAN_DETAILS[newPlan] || newPlan === settings.plan) return;
        try {
            setCheckoutLoading(true);

            const isCurrentPlanExpired = settings.is_expired || settings.remaining_days <= 0;
            const isPaidPlan = newPlan !== 'Free';
            const isFreePlan = settings.plan === 'Free' || !settings.plan;

            // Define plan tiers for upgrade/downgrade detection
            const planTiers = { 'Free': 0, 'Pro Business': 1, 'Enterprise': 2 };
            const currentTier = planTiers[settings.plan] || 0;
            const newTier = planTiers[newPlan] || 0;
            const isUpgrade = newTier > currentTier;
            const isDowngrade = newTier < currentTier;

            console.log(`[INFO] Plan change: ${settings.plan} (tier ${currentTier}) → ${newPlan} (tier ${newTier}), Upgrade: ${isUpgrade}, Downgrade: ${isDowngrade}`);

            // If switching to Free, no payment needed
            if (newPlan === 'Free') {
                await persistFreePlan(newPlan);
                setMessage('Plan changed to Free. You no longer have paid features.');
                setTimeout(() => setMessage(''), 3000);
                return;
            }

            // If switching to a paid plan
            if (isPaidPlan) {
                // Case 1: On Free plan or subscription expired → Always ask for payment
                if (isFreePlan || isCurrentPlanExpired) {
                    console.log('[INFO] Asking for payment - either on Free or plan expired');
                    await startRazorpayCheckout(newPlan);
                }
                // Case 2: Active subscription - UPGRADE (higher tier) → Ask for payment
                else if (isUpgrade) {
                    console.log('[INFO] Upgrading to higher tier - asking for payment');
                    await startRazorpayCheckout(newPlan);
                }
                // Case 3: Active subscription - DOWNGRADE (lower tier) → No payment
                else if (isDowngrade) {
                    console.log('[INFO] Downgrading to lower tier - no payment');
                    await persistFreePlan(newPlan);
                    const daysLeft = settings.remaining_days || 365;
                    setMessage(`Successfully downgraded to ${newPlan}! Your subscription is valid for ${daysLeft} more days.`);
                    setTimeout(() => setMessage(''), 4000);
                }
            }
        } catch (err) {
            const msg = err?.message || 'Unable to process plan change';
            if (msg.toLowerCase().includes('session expired')) {
                setMessage('Session expired for billing request. Please use Save Changes or re-open billing and retry.');
                return;
            }
            if (msg.toLowerCase().includes('razorpay credentials are not configured')) {
                setMessage('Add RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in backend .env, then restart backend.');
            } else {
                setMessage(msg);
            }
        } finally {
            setCheckoutLoading(false);
        }

        }));
    };
    const handleCardUpdate = (field, value) => {
        setSettings(prev => ({ ...prev, [field]: value }));
    };
    // const handleChangePassword = async (e) => {
    //     e.preventDefault();
    //     if (passwordForm.new !== passwordForm.confirm) {
    //         setMessage("Passwords do not match");
    //         return;
    //     }
        
    //     const res = await apiFetch('/api/change-password', {
    //         method: 'POST',
    //         headers: { 'Content-Type': 'application/json' },
    //         body: JSON.stringify({
    //             current_password: passwordForm.current,
    //             new_password: passwordForm.new
    //         })
    //     });

    //     if (res.ok) {
    //         setMessage('Password changed successfully');
    //         setPasswordForm({ current: '', new: '', confirm: '' });
    //     } else {
    //         setMessage('Password change failed');
    //     }
    // };
    const handleChangePassword = async (e) => {
        e.preventDefault();
        
        // 1. Basic client-side validation
        if (passwordForm.new !== passwordForm.confirm) {
            setMessage("Passwords do not match");
            return;
        }

        try {
            const res = await apiFetch('/api/change-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    current: passwordForm.current, // Changed from current_password
                    new: passwordForm.new,         // Changed from new_password
                    confirm: passwordForm.confirm  // Added this
                })
            });

            const data = await res.json();

            if (res.ok) {
                setMessage('Password changed successfully');
                setPasswordForm({ current: '', new: '', confirm: '' });
            } else {
                // Display the specific error from the backend (like "Current password incorrect")
                setMessage(data.detail || 'Password change failed');
            }
        } catch (err) {
            setMessage('System error. Please try again.');
            console.error(err);
        }
    };

    const handleDiscard = () => {
        setForm({ ...profile });
        setMessage('Changes discarded');
        setTimeout(() => setMessage(''), 2000);
    };

    useEffect(() => {
        if (autoUpgradeHandledRef.current) return;
        const pendingPlan = localStorage.getItem('pendingUpgradePlan');
        if (!pendingPlan || !PLAN_DETAILS[pendingPlan]) return;
        autoUpgradeHandledRef.current = true;
        localStorage.removeItem('pendingUpgradePlan');
        if (pendingPlan !== settings.plan) {
            handlePlanChange(pendingPlan);
        }
    }, [settings.plan]);

    return (
        <DashboardLayout title="Settings">
            <div className="max-w-5xl mx-auto space-y-12 pb-20">
                {/* Header */}
                <div className="flex items-center justify-between border-b border-white/5 pb-10">
                    <div>
                        <h1 className="text-4xl font-black text-white tracking-tight">Settings</h1>
                        <p className="text-slate-400 text-lg mt-2">Manage your account settings and preferences.</p>
                    </div>
                    <div className="flex gap-4">
                        <button onClick={handleDiscard} className="px-8 py-3 bg-white/5 border border-white/10 rounded-2xl text-sm font-bold hover:bg-white/10 transition-all">Discard</button>
                        <button onClick={handleSave} disabled={saving} className="px-8 py-3 bg-primary text-background-dark rounded-2xl text-sm font-black shadow-lg shadow-primary/20 hover:scale-105 transition-all disabled:opacity-50">
                            {saving ? 'Saving...' : 'Save Changes'}
                        </button>
                    </div>
                </div>

                <AnimatePresence>
                    {message && (
                        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="p-4 bg-primary/10 border border-primary/20 rounded-2xl text-primary font-bold flex items-center gap-2">
                            <CheckCircle2 className="w-5 h-5" /> {message}
                        </motion.div>
                    )}
                </AnimatePresence>
                <AnimatePresence>
                    {paymentModal.open && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-6"
                        >
                            <motion.div
                                initial={{ opacity: 0, y: 20, scale: 0.95 }}
                                animate={{ opacity: 1, y: 0, scale: 1 }}
                                exit={{ opacity: 0, y: 10, scale: 0.97 }}
                                className="w-full max-w-xl bg-background-dark border border-primary/30 rounded-[2rem] p-8 shadow-[0_0_40px_rgba(13,204,242,0.2)]"
                            >
                                <div className="flex items-center gap-4 mb-6">
                                    <div className="w-14 h-14 rounded-2xl bg-emerald-500/20 border border-emerald-400/30 flex items-center justify-center">
                                        <CheckCircle2 className="w-8 h-8 text-emerald-400" />
                                    </div>
                                    <div>
                                        <h3 className="text-2xl font-black text-white">Payment Successful</h3>
                                        <p className="text-slate-400 text-sm mt-1">Your account has been upgraded successfully.</p>
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
                                    <div className="rounded-xl bg-white/[0.03] border border-white/10 p-4">
                                        <p className="text-[10px] uppercase tracking-widest text-slate-500 font-black">Upgraded Plan</p>
                                        <p className="text-lg font-bold text-white mt-2">{paymentModal.plan}</p>
                                    </div>
                                    <div className="rounded-xl bg-white/[0.03] border border-white/10 p-4">
                                        <p className="text-[10px] uppercase tracking-widest text-slate-500 font-black">Amount Paid</p>
                                        <p className="text-lg font-bold text-primary mt-2">{paymentModal.price}</p>
                                    </div>
                                </div>

                                {paymentModal.paymentId && (
                                    <p className="text-xs text-slate-500 mb-6">
                                        Payment ID: <span className="text-slate-300 font-semibold">{paymentModal.paymentId}</span>
                                    </p>
                                )}

                                <div className="flex justify-end gap-3">
                                    <button
                                        onClick={() => setPaymentModal({ open: false, plan: '', price: '', paymentId: '' })}
                                        className="px-5 py-2.5 bg-primary text-background-dark rounded-xl font-black text-xs uppercase tracking-widest hover:brightness-110 transition-all"
                                    >
                                        Continue
                                    </button>
                                </div>
                            </motion.div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Profile Section - Fixed Empty Values & Added Image Upload */}
                <section className="space-y-8">
                    <h3 className="text-2xl font-bold flex items-center gap-3">
                        <User className="w-6 h-6 text-primary" /> Public Profile
                    </h3>
                    <div className="bg-white/[0.03] border border-white/10 rounded-[3rem] p-10">
                        <div className="flex flex-col md:flex-row gap-12 items-start">
                            
                            {/* Profile Picture Upload Logic */}
                            <div className="relative group">
                                <button onClick={() => fileInputRef.current.click()} className="w-40 h-40 rounded-full border-4 border-white/10 overflow-hidden bg-white/5 relative">
                                    <img 
                                        src={settings.profilePictureUrl || `https://ui-avatars.com/api/?name=${form.firstname}+${form.lastname}&background=0DCAF0&color=fff`} 
                                        className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" 
                                        alt="Profile" 
                                    />
                                    <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                                        <Camera className="w-8 h-8 text-white" />
                                    </div>
                                </button>
                                {/* Hidden Input For Picture Selection */}
                                <input 
                                    type="file" 
                                    ref={fileInputRef} 
                                    onChange={onProfilePictureChange} 
                                    style={{ display: 'none' }} 
                                    accept="image/*"
                                />
                                <button onClick={() => fileInputRef.current.click()} className="absolute bottom-2 right-2 p-3 bg-primary text-background-dark rounded-full shadow-xl border-4 border-background-dark">
                                    <Camera className="w-5 h-5 font-bold" />
                                </button>
                            </div>


                            <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-8 w-full">
                                <div className="space-y-3">
                                    <label className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">First Name</label>
                                    <input
                                        className="w-full px-6 py-4 bg-white/5 border border-white/10 rounded-2xl focus:ring-2 focus:ring-primary/50 outline-none text-white transition-all"
                                        value={form.firstname}
                                        onChange={e => handleProfileChange('firstname', e.target.value)}
                                        placeholder="Enter first name"
                                    />
                                </div>
                                <div className="space-y-3">
                                    <label className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">Last Name</label>
                                    <input
                                        className="w-full px-6 py-4 bg-white/5 border border-white/10 rounded-2xl focus:ring-2 focus:ring-primary/50 outline-none text-white transition-all"
                                        value={form.lastname}
                                        onChange={e => handleProfileChange('lastname', e.target.value)}
                                        placeholder="Enter last name"
                                    />
                                </div>
                                <div className="space-y-3 md:col-span-2">
                                    <label className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">Email Address</label>
                                    <div className="relative group">
                                        <Mail className="absolute left-6 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-primary transition-colors" />
                                        <input
                                            className="w-full pl-16 pr-6 py-4 bg-white/5 border border-white/10 rounded-2xl focus:ring-2 focus:ring-primary/50 outline-none text-white transition-all"
                                            value={form.email}
                                            onChange={e => handleProfileChange('email', e.target.value)}
                                            placeholder="Enter your email"
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                {/* Security - Redesigned Password Layout */}
                <section className="space-y-8">
                    <h3 className="text-2xl font-bold flex items-center gap-3">
                        <Shield className="w-6 h-6 text-primary" /> Security
                    </h3>
                    <div className="bg-white/[0.03] border border-white/10 rounded-[3rem] divide-y divide-white/5 overflow-hidden">
                        <div className="p-10">
                            <div className="flex flex-col lg:flex-row gap-10">
                                <div className="lg:w-1/3">
                                    <p className="font-bold text-lg flex items-center gap-2"><KeyRound className="w-5 h-5 text-primary" /> Password</p>
                                    <p className="text-slate-500 mt-1">Update your account password to stay secure.</p>
                                </div>
                                <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-4">
                                    <input type="password" placeholder="Current" className="px-6 py-4 bg-white/5 border border-white/10 rounded-2xl text-white outline-none focus:border-primary/50" value={passwordForm.current} onChange={e => setPasswordForm({ ...passwordForm, current: e.target.value })} />
                                    <input type="password" placeholder="New" className="px-6 py-4 bg-white/5 border border-white/10 rounded-2xl text-white outline-none focus:border-primary/50" value={passwordForm.new} onChange={e => setPasswordForm({ ...passwordForm, new: e.target.value })} />
                                    <input type="password" placeholder="Confirm" className="px-6 py-4 bg-white/5 border border-white/10 rounded-2xl text-white outline-none focus:border-primary/50" value={passwordForm.confirm} onChange={e => setPasswordForm({ ...passwordForm, confirm: e.target.value })} />
                                    <div className="md:col-span-3 flex justify-end">
                                        <button onClick={handleChangePassword} className="px-6 py-3 bg-white/5 border border-white/10 rounded-xl text-xs font-black uppercase tracking-widest hover:bg-white/10 transition-all">Update Password</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div className="p-10 flex items-center justify-between hover:bg-white/[0.01] transition-colors">
                            <div>
                                <div className="flex items-center gap-3">
                                    <p className="font-bold text-lg">Two-Factor Authentication (2FA)</p>
                                    {settings.twoFactorEnabled && <span className="px-3 py-1 rounded-full bg-emerald-400/10 text-emerald-400 text-[10px] font-black uppercase tracking-widest">Active</span>}
                                </div>
                                <p className="text-slate-500 mt-1">Extra layer of security for your account via authenticator app.</p>
                            </div>
                            <button className={`px-6 py-3 rounded-xl text-xs font-black uppercase tracking-widest transition-all ${settings.twoFactorEnabled ? 'bg-rose-500/10 text-rose-500 border border-rose-500/20 hover:bg-rose-500/20' : 'bg-primary/10 text-primary border border-primary/20 hover:bg-primary/20'}`} onClick={() => toggleSetting('twoFactorEnabled')}>
                                {settings.twoFactorEnabled ? 'Disable' : 'Enable'}
                            </button>
                        </div>
                    </div>
                </section>

                {/* Notifications */}
                <section className="space-y-8">
                    <h3 className="text-2xl font-bold flex items-center gap-3">
                        <Bell className="w-6 h-6 text-primary" /> Notifications
                    </h3>
                    <div className="bg-white/[0.03] border border-white/10 rounded-[3rem] p-10 space-y-10">
                        {[
                            { id: 'emailAlerts', label: 'Email Alerts', desc: 'Weekly trend summaries and account activity.' },
                            { id: 'systemUpdates', label: 'System Updates', desc: 'Get notified about new features and scheduled maintenance.' }
                        ].map((item) => (
                            <div key={item.id} className="flex items-center justify-between group">
                                <div>
                                    <p className="font-bold text-lg group-hover:text-primary transition-colors">{item.label}</p>
                                    <p className="text-slate-500 mt-1">{item.desc}</p>
                                </div>
                                <button onClick={() => toggleSetting(item.id)} className={`w-14 h-8 rounded-full relative transition-colors ${settings[item.id] ? 'bg-primary' : 'bg-white/10'}`}>
                                    <motion.div animate={{ x: settings[item.id] ? 28 : 4 }} className="absolute top-1 w-6 h-6 bg-white rounded-full shadow-lg" />
                                </button>
                            </div>
                        ))}
                    </div>
                </section>

                {/* Billing */}
                <section ref={billingRef} className="space-y-8">
                    <h3 className="text-2xl font-bold flex items-center gap-3">
                        <CreditCard className="w-6 h-6 text-primary" /> Billing
                    </h3>
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                        <div className="lg:col-span-2 bg-white/[0.03] border border-white/10 rounded-[3rem] p-10 flex flex-col justify-between">
                            <div>
                                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500 mb-6">Active Plan</p>
                                <div className="flex items-start justify-between gap-6">
                                    <div>
                                        <h4 className="text-4xl font-black text-white">{settings.plan}</h4>
                                        <p className="text-slate-400 mt-2 text-lg">{settings.price} / month</p>
                                        <p className="text-xs mt-3 inline-flex items-center px-3 py-1 rounded-full bg-primary/10 text-primary border border-primary/20 font-black uppercase tracking-widest">
                                            {PLAN_TAGS[settings.plan] || 'Plan'}
                                        </p>

                                        {/* New: Show subscription status */}
                                        {settings.plan_expiry_date && (
                                            <div className="mt-5 p-4 bg-white/[0.03] border border-white/10 rounded-2xl">
                                                <p className="text-xs text-slate-400 font-bold uppercase tracking-widest mb-2">Subscription Status</p>
                                                {settings.is_expired ? (
                                                    <p className="text-sm text-red-400 font-bold">Plan Expired - Reverted to Free</p>
                                                ) : (
                                                    <>
                                                        <p className="text-sm text-emerald-400 font-bold">Active</p>
                                                        <p className="text-xs text-slate-400 mt-2">
                                                            Active until: <span className="text-white font-bold">
                                                                {new Date(settings.plan_expiry_date).toLocaleDateString()}
                                                            </span>
                                                        </p>
                                                        <p className="text-xs text-slate-400 mt-1">
                                                            Days remaining: <span className="text-primary font-bold">{settings.remaining_days || 0} days</span>
                                                        </p>
                                                    </>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                    {checkoutLoading && (
                                        <div className="text-xs font-black uppercase tracking-widest text-primary">Processing payment...</div>
                                    )}
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
                                    {Object.entries(PLAN_DETAILS).map(([planName, details]) => {
                                        const isCurrent = settings.plan === planName;
                                        const isPaid = details.amountInr > 0;

                                        // Check if user has active paid subscription (not Free or expired)
                                        const hasActivePaidSubscription = settings.subscription_status === 'active' && settings.plan !== 'Free' && !settings.is_expired;

                                        // Define plan tier order
                                        const planOrder = { 'Free': 0, 'Pro Business': 1, 'Enterprise': 2 };
                                        const currentPlanOrder = planOrder[settings.plan] || 0;
                                        const newPlanOrder = planOrder[planName] || 0;
                                        const isUpgrade = newPlanOrder > currentPlanOrder;
                                        const isDowngrade = newPlanOrder < currentPlanOrder;

                                        // If user has active paid plan, only show current plan + upgrades
                                        // Hide all downgrade options and Free plan
                                        if (hasActivePaidSubscription) {
                                            if (!isCurrent && !isUpgrade) {
                                                return null; // Hide all downgrades and Free plan
                                            }
                                        }

                                        return (
                                            <button
                                                key={planName}
                                                onClick={() => handlePlanChange(planName)}
                                                disabled={checkoutLoading || isCurrent || (hasActivePaidSubscription && isDowngrade)}
                                                className={`text-left rounded-2xl p-5 border transition-all ${isCurrent
                                                    ? 'border-primary bg-primary/15 shadow-[0_0_24px_rgba(13,204,242,0.18)]'
                                                    : 'border-white/10 bg-white/[0.02] hover:border-primary/40 hover:bg-white/[0.04]'
                                                } ${checkoutLoading || (hasActivePaidSubscription && isDowngrade) ? 'opacity-60 cursor-not-allowed' : ''}`}
                                            >
                                                <div className="flex items-center justify-between gap-2 mb-2">
                                                    <p className="font-black text-sm text-white">{planName}</p>
                                                    <span className={`text-[10px] px-2 py-1 rounded-full font-black uppercase tracking-widest ${isPaid ? 'bg-white/10 text-slate-300' : 'bg-emerald-500/15 text-emerald-400'}`}>
                                                        {PLAN_TAGS[planName]}
                                                    </span>
                                                </div>
                                                <p className="text-primary text-lg font-black">{details.price}</p>
                                                <p className="text-xs text-slate-400 mt-2">AI {details.ai}% • Storage {details.storage}%</p>

                                                {/* Smart button text based on subscription status */}
                                                <p className="text-[11px] mt-4 font-black uppercase tracking-wider text-slate-300">
                                                    {isCurrent ? (
                                                        settings.subscription_status === 'active'
                                                            ? `Current Plan (${settings.remaining_days} days left)`
                                                            : 'Current Plan'
                                                    ) : isPaid ? (
                                                        // Calculate tier for upgrade/downgrade detection
                                                        (() => {
                                                            const planTiers = { 'Free': 0, 'Pro Business': 1, 'Enterprise': 2 };
                                                            const currentTier = planTiers[settings.plan] || 0;
                                                            const newTier = planTiers[planName] || 0;
                                                            const isUpgrade = newTier > currentTier;
                                                            const isDowngrade = newTier < currentTier;

                                                            // If on Free or expired: always ask for payment
                                                            if (settings.plan === 'Free' || settings.is_expired || !settings.subscription_status || settings.subscription_status === 'none') {
                                                                return 'Upgrade with Razorpay';
                                                            }
                                                            // If upgrading to higher tier: ask for payment
                                                            if (isUpgrade) {
                                                                return 'Upgrade with Razorpay';
                                                            }
                                                            // If downgrading to lower tier: no payment
                                                            if (isDowngrade) {
                                                                return 'Downgrade (No Payment)';
                                                            }
                                                            return 'Upgrade with Razorpay';
                                                        })()
                                                    ) : (
                                                        // If switching to Free (only shown if no active subscription)
                                                        'Switch to Free'
                                                    )}
                                                </p>
                                            </button>
                                        );
                                    })}
                                <div className="flex items-center justify-between">
                                    <div>
                                        <h4 className="text-4xl font-black text-white">{settings.plan}</h4>
                                        {/* Dynamic Price */}
                                        <p className="text-slate-400 mt-2 text-lg">{settings.price} / month</p>
                                    </div>
                                    <select 
                                        className="bg-background-dark border border-white/10 rounded-xl px-4 py-2 text-white outline-none focus:ring-2 focus:ring-primary/50"
                                        value={settings.plan}
                                        onChange={e => handlePlanChange(e.target.value)}
                                    >
                                        {Object.keys(PLAN_DETAILS).map(planName => (
                                            <option key={planName} value={planName}>{planName}</option>
                                        ))}
                                    </select>
                                </div>
                            </div>
                            
                            <div className="mt-12 pt-10 border-t border-white/5">
                                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500 mb-6">Payment Method</p>
                                <div className="flex items-center gap-6">
                                    <div className="w-20 h-12 bg-white/5 border border-white/10 rounded-xl flex items-center justify-center">
                                        <CreditCard className="w-6 h-6 text-slate-400" />
                                    </div>
                                    <div className="flex-1">
                                        {/* Dynamic Card Details */}
                                        <p className="font-bold text-lg">
                                            {settings.cardLast4 ? `Visa ending in ${settings.cardLast4}` : 'No card linked'}
                                        </p>
                                        <p className="text-sm text-slate-500">
                                            {settings.cardExpiry ? `Expires ${settings.cardExpiry}` : 'Update payment info'}
                                        </p>
                                    </div>
                                    <button className="text-sm font-black text-primary hover:underline uppercase tracking-widest">Edit</button>
                                </div>
                            </div>
                        </div>

                        <div className="bg-primary/5 border border-primary/20 rounded-[3rem] p-10 flex flex-col justify-between">
                            <div>
                                <p className="text-[10px] font-black text-primary uppercase tracking-[0.2em] mb-8">Usage This Month</p>
                                <div className="space-y-8">
                                    {[
                                        { label: 'AI Generations', val: settings.usage.ai },
                                        { label: 'Data Storage', val: settings.usage.storage },
                                    ].map(stat => (
                                        <div key={stat.label}>
                                            <div className="flex justify-between text-xs font-black uppercase tracking-widest mb-3">
                                                <span>{stat.label}</span>
                                                <span className="text-primary">{stat.val}%</span>
                                            </div>
                                            <div className="h-3 bg-background-dark rounded-full overflow-hidden p-[2px]">
                                                <motion.div
                                                    initial={false} // Prevents jumpy animation on first load
                                                    animate={{ width: `${stat.val}%` }}
                                                    transition={{ type: "spring", stiffness: 100, damping: 20 }}
                                                    className="h-full bg-primary rounded-full shadow-[0_0_15px_rgba(13,204,242,0.3)]"
                                                />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                            <p className="text-xs text-slate-500 mt-10 italic leading-relaxed">
                                {settings.plan === 'Enterprise' 
                                    ? "You're on our highest tier. Contact support for custom limits." 
                                    : "Need more capacity? Upgrading boosts your AI and storage limits instantly."}
                            </p>
                        </div>
                    </div>
                </section>
            </div>
        </DashboardLayout>
    );
};

export default Settings;
