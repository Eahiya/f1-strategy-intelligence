import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Eye, EyeOff, Lock, User, AlertCircle, CheckCircle, Shield, ChevronRight, Zap } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const LoginPage = () => {
  const navigate = useNavigate();
  const { login, error: authError } = useAuth();
  
  const [formData, setFormData] = useState({ username: '', password: '' });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const validateForm = () => {
    if (!formData.username.trim()) { setError('Username is required'); return false; }
    if (!formData.password) { setError('Password is required'); return false; }
    if (formData.password.length < 4) { setError('Password must be at least 4 characters'); return false; }
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (!validateForm()) return;
    setLoading(true);
    const result = await login(formData.username, formData.password);
    setLoading(false);
    if (result.success) {
      setSuccess(true);
      setTimeout(() => navigate('/'), 1000);
    } else {
      setError(result.error || authError);
    }
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError('');
  };

  const trackLines = Array.from({ length: 20 }, (_, i) => i);

  return (
    <div className="relative min-h-screen bg-[#050505] flex items-center justify-center p-4 overflow-hidden">
      {/* Animated background grid */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.015)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.015)_1px,transparent_1px)] bg-[size:80px_80px]" />
      
      {/* Radial glow */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_50%_0%,rgba(225,6,0,0.12)_0%,transparent_60%)]" />
      
      {/* Animated track lines */}
      {trackLines.map((i) => (
        <motion.div
          key={i}
          className="absolute h-px bg-gradient-to-r from-transparent via-[#e10600]/10 to-transparent"
          style={{ top: `${(i + 1) * 5}%`, left: 0, right: 0 }}
          initial={{ opacity: 0, scaleX: 0 }}
          animate={{ opacity: [0.2, 0.6, 0.2], scaleX: [0, 1, 0] }}
          transition={{
            duration: 4 + i * 0.3,
            repeat: Infinity,
            delay: i * 0.2,
          }}
        />
      ))}

      {/* Corner accents */}
      <motion.div
        className="absolute top-0 left-0 w-32 h-32 border-l-2 border-t-2 border-[#e10600]/20"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5, duration: 1 }}
      />
      <motion.div
        className="absolute bottom-0 right-0 w-32 h-32 border-r-2 border-b-2 border-[#e10600]/20"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.7, duration: 1 }}
      />

      {/* Main card */}
      <motion.div
        initial={{ opacity: 0, y: 40, scale: 0.95 }}
        animate={mounted ? { opacity: 1, y: 0, scale: 1 } : {}}
        transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        className="relative w-full max-w-md"
      >
        {/* Top accent line */}
        <div className="absolute -top-px left-12 right-12 h-px bg-gradient-to-r from-transparent via-[#e10600] to-transparent" />

        <div className="bg-[#0a0a0a]/90 backdrop-blur-xl border border-white/[0.06] rounded-2xl overflow-hidden">
          {/* Header section */}
          <div className="relative px-8 pt-10 pb-8 border-b border-white/[0.06]">
            {/* Animated F1 badge */}
            <motion.div
              className="flex items-center justify-center mb-6"
              initial={{ scale: 0.5, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
            >
              <div className="relative">
                <div className="w-20 h-20 bg-gradient-to-br from-[#e10600] to-[#b91c1c] rounded-2xl flex items-center justify-center shadow-[0_8px_32px_rgba(225,6,0,0.3)]">
                  <span className="text-3xl font-black text-white italic tracking-tighter">F1</span>
                </div>
                {/* Pulsing ring */}
                <motion.div
                  className="absolute inset-0 rounded-2xl border-2 border-[#e10600]"
                  animate={{ scale: [1, 1.15], opacity: [0.5, 0] }}
                  transition={{ duration: 2, repeat: Infinity }}
                />
              </div>
            </motion.div>

            {/* Title */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="text-center"
            >
              <h1 className="text-2xl font-black text-white tracking-tight mb-1">
                Strategy<span className="text-[#e10600]">Command</span>
              </h1>
              <p className="text-xs text-white/30 uppercase tracking-[0.2em]">Race Control Access</p>
            </motion.div>

            {/* Status bar */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4 }}
              className="flex items-center justify-center gap-4 mt-5"
            >
              <div className="flex items-center gap-2 px-3 py-1.5 bg-white/[0.03] rounded-full border border-white/[0.06]">
                <Shield className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-[11px] text-white/40">Encrypted</span>
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 bg-white/[0.03] rounded-full border border-white/[0.06]">
                <Zap className="w-3.5 h-3.5 text-[#e10600]" />
                <span className="text-[11px] text-white/40">v6.3</span>
              </div>
            </motion.div>
          </div>

          {/* Form section */}
          <div className="px-8 py-8">
            {/* Error/Success messages */}
            <div className="min-h-[56px] mb-6">
              <AnimatePresence mode="wait">
                {error && (
                  <motion.div
                    initial={{ opacity: 0, y: -8, height: 0 }}
                    animate={{ opacity: 1, y: 0, height: 'auto' }}
                    exit={{ opacity: 0, y: -8, height: 0 }}
                    className="p-3 bg-red-500/[0.08] border border-red-500/20 rounded-xl flex items-center gap-3"
                  >
                    <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
                    <p className="text-sm text-red-400">{error}</p>
                  </motion.div>
                )}
                {success && (
                  <motion.div
                    initial={{ opacity: 0, y: -8, height: 0 }}
                    animate={{ opacity: 1, y: 0, height: 'auto' }}
                    exit={{ opacity: 0, y: -8, height: 0 }}
                    className="p-3 bg-emerald-500/[0.08] border border-emerald-500/20 rounded-xl flex items-center gap-3"
                  >
                    <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                    <p className="text-sm text-emerald-400">Access granted. Redirecting...</p>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Username */}
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 }}
              >
                <label className="block text-[10px] font-semibold text-white/25 uppercase tracking-[0.15em] mb-2">
                  Username
                </label>
                <div className="relative group">
                  <User className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20 group-focus-within:text-[#e10600] transition-colors" />
                  <input
                    type="text"
                    name="username"
                    value={formData.username}
                    onChange={handleChange}
                    disabled={loading || success}
                    className="w-full bg-white/[0.03] border border-white/[0.06] rounded-xl py-3.5 pl-11 pr-4 text-white placeholder-white/15 focus:border-[#e10600]/50 focus:outline-none focus:ring-1 focus:ring-[#e10600]/20 transition-all disabled:opacity-50 text-sm"
                    placeholder="Enter your username"
                    autoComplete="username"
                  />
                </div>
              </motion.div>

              {/* Password */}
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.5 }}
              >
                <label className="block text-[10px] font-semibold text-white/25 uppercase tracking-[0.15em] mb-2">
                  Password
                </label>
                <div className="relative group">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20 group-focus-within:text-[#e10600] transition-colors" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    disabled={loading || success}
                    className="w-full bg-white/[0.03] border border-white/[0.06] rounded-xl py-3.5 pl-11 pr-12 text-white placeholder-white/15 focus:border-[#e10600]/50 focus:outline-none focus:ring-1 focus:ring-[#e10600]/20 transition-all disabled:opacity-50 text-sm"
                    placeholder="Enter your password"
                    autoComplete="current-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-white/20 hover:text-white/40 transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </motion.div>

              {/* Submit */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6 }}
              >
                <motion.button
                  type="submit"
                  disabled={loading || success}
                  whileHover={!loading && !success ? { scale: 1.01 } : {}}
                  whileTap={!loading && !success ? { scale: 0.99 } : {}}
                  className="w-full py-4 bg-gradient-to-r from-[#e10600] to-[#b91c1c] rounded-xl font-bold text-white text-sm uppercase tracking-wider shadow-[0_4px_20px_rgba(225,6,0,0.3)] hover:shadow-[0_8px_30px_rgba(225,6,0,0.4)] transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3 relative overflow-hidden group"
                >
                  {/* Shimmer overlay */}
                  <motion.div
                    className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent"
                    initial={{ x: '-100%' }}
                    animate={{ x: '100%' }}
                    transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}
                  />
                  
                  {loading ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                      <span>Authenticating</span>
                    </>
                  ) : (
                    <>
                      <span>Access Race Control</span>
                      <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                    </>
                  )}
                </motion.button>
              </motion.div>
            </form>
          </div>

          {/* Footer */}
          <div className="px-8 py-6 border-t border-white/[0.06] bg-white/[0.01]">
            <div className="flex items-center justify-between">
              <div className="text-xs text-white/20">
                Don&apos;t have access?{' '}
                <span className="text-[#e10600]/60 hover:text-[#e10600] cursor-pointer transition-colors font-medium">
                  Contact Admin
                </span>
              </div>
              <div className="flex items-center gap-1.5 text-[10px] text-white/15">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-f1-pulse-dot" />
                Systems Online
              </div>
            </div>
          </div>
        </div>

        {/* Bottom glow */}
        <div className="absolute -bottom-20 left-1/2 -translate-x-1/2 w-64 h-40 bg-[#e10600]/10 blur-[80px] pointer-events-none" />
      </motion.div>
    </div>
  );
};

export default LoginPage;
