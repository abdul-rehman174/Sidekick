import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import {
  Send, Sparkles, Bell, CheckCircle, Clock, ChevronLeft, ChevronRight,
  Trash2, History, User as UserIcon, Lock, X, Settings, Wand2, Heart,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';
const POLL_INTERVAL_MS = 5000;

const authHeaders = () => {
  const token = localStorage.getItem('sidekick_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

const clearSession = () => {
  localStorage.removeItem('sidekick_user');
  localStorage.removeItem('sidekick_token');
};

const formatRemainingTime = (dueAt) => {
  if (!dueAt) return 'Pending';
  const due = new Date(dueAt.includes('Z') ? dueAt : dueAt + 'Z');
  const diffMs = due - new Date();
  if (diffMs <= 0) return 'Due now';
  const mins = Math.floor(diffMs / 60000);
  const hours = Math.floor(mins / 60);
  return hours > 0 ? `${hours}h ${mins % 60}m` : `${mins}m`;
};

function App() {
  const [user, setUser] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [reminders, setReminders] = useState([]);
  const [historyReminders, setHistoryReminders] = useState([]);
  const [viewMode, setViewMode] = useState('active');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isPersonaModalOpen, setIsPersonaModalOpen] = useState(false);
  const [persona, setPersona] = useState({ persona_name: '', behavior_profile: '', system_instruction: '' });
  const [activeNotification, setActiveNotification] = useState(null);
  const [onboardingForm, setOnboardingForm] = useState({ username: '', personaName: '', password: '' });
  const [authMode, setAuthMode] = useState('login');
  const [authError, setAuthError] = useState('');
  const [authNotice, setAuthNotice] = useState('');
  const [compressing, setCompressing] = useState(false);
  // TOKEN_COUNTER: session totals for debug UI — remove when done testing
  const [sessionTokens, setSessionTokens] = useState({ prompt: 0, completion: 0, total: 0, calls: 0 });
  const [lastCompressTokens, setLastCompressTokens] = useState(null);

  const scrollRef = useRef(null);
  const mainRef = useRef(null);
  const shouldAutoScrollRef = useRef(true);
  const buzzedRemindersRef = useRef(new Set());

  const handleMainScroll = () => {
    const el = mainRef.current;
    if (!el) return;
    shouldAutoScrollRef.current = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
  };

  useEffect(() => {
    const savedUser = localStorage.getItem('sidekick_user');
    const savedToken = localStorage.getItem('sidekick_token');
    if (savedUser && savedToken) {
      setUser(JSON.parse(savedUser));
    }
  }, []);

  useEffect(() => {
    if (!user?.id) return;
    loadInitialData();
  }, [user?.id]);

  useEffect(() => {
    if (!user?.id) return;
    const interval = setInterval(() => {
      fetchReminders();
    }, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [user?.id, viewMode]);

  useEffect(() => {
    if (shouldAutoScrollRef.current) {
      scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const handleAuthError = (err) => {
    if (err.response?.status === 401) {
      clearSession();
      setUser(null);
      return true;
    }
    return false;
  };

  const loadInitialData = async () => {
    try {
      const [chatRes, personaRes] = await Promise.all([
        axios.get(`${API_BASE}/api/chat/history`, { headers: authHeaders() }),
        axios.get(`${API_BASE}/api/persona`, { headers: authHeaders() }),
      ]);
      setMessages(chatRes.data.reverse().map(msg => ({
        role: msg.role === 'user' ? 'user' : 'bot',
        content: msg.content,
      })));
      setPersona({
        persona_name: personaRes.data.persona_name || '',
        behavior_profile: personaRes.data.behavior_profile || '',
        system_instruction: personaRes.data.system_instruction || '',
      });
      fetchReminders();
    } catch (err) {
      console.error('Initial load failed:', err);
      handleAuthError(err);
    }
  };

  const triggerSensoryAlert = (text) => {
    try {
      const utterance = new SpeechSynthesisUtterance(text);
      window.speechSynthesis.speak(utterance);
    } catch {}
    setActiveNotification(text);
    setTimeout(() => setActiveNotification(null), 5000);
  };

  const fetchReminders = async () => {
    try {
      const status = viewMode === 'active' ? 'pending' : 'completed';
      const res = await axios.get(`${API_BASE}/api/reminders?status=${status}`, { headers: authHeaders() });
      if (viewMode === 'active') {
        setReminders(res.data);
        const now = new Date();
        res.data.forEach(r => {
          if (!r.due_at) return;
          const due = new Date(r.due_at.includes('Z') ? r.due_at : r.due_at + 'Z');
          if (due <= now && !buzzedRemindersRef.current.has(r.id)) {
            triggerSensoryAlert(`Reminder: ${r.task}`);
            buzzedRemindersRef.current.add(r.id);
            axios.post(`${API_BASE}/api/reminders/${r.id}/complete`, {}, { headers: authHeaders() })
              .then(fetchReminders)
              .catch(() => {});
          }
        });
      } else {
        setHistoryReminders(res.data);
      }
    } catch (err) {
      handleAuthError(err);
    }
  };

  const handleOnboard = async (e) => {
    e.preventDefault();
    setAuthError('');
    setAuthNotice('');
    if (!onboardingForm.username || !onboardingForm.password) return;
    setLoading(true);
    try {
      if (authMode === 'register') {
        await axios.post(`${API_BASE}/api/register`, {
          username: onboardingForm.username,
          password: onboardingForm.password,
          persona_name: onboardingForm.personaName || 'Sidekick',
        });
        setAuthMode('login');
        setAuthNotice('Account created — sign in below 💕');
        setOnboardingForm(f => ({ username: f.username, personaName: '', password: '' }));
        return;
      }

      const res = await axios.post(`${API_BASE}/api/login`, {
        username: onboardingForm.username,
        password: onboardingForm.password,
      });
      const newUser = {
        id: res.data.user_id,
        username: res.data.username,
        personaName: res.data.persona_name,
      };
      localStorage.setItem('sidekick_user', JSON.stringify(newUser));
      localStorage.setItem('sidekick_token', res.data.access_token);
      setUser(newUser);
      setMessages([]);
      if (Notification?.permission && Notification.permission !== 'granted') {
        Notification.requestPermission();
      }
    } catch (err) {
      const status = err.response?.status;
      if (status === 401) {
        setAuthError('Wrong username or password.');
      } else if (status === 409) {
        setAuthError('That username is already taken — try logging in instead.');
      } else if (status === 422) {
        setAuthError('Username is required and password must be at least 8 characters.');
      } else {
        setAuthError(authMode === 'register' ? 'Registration failed. Try again.' : 'Login failed. Try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async (e) => {
    e?.preventDefault();
    if (!input.trim() || loading) return;
    shouldAutoScrollRef.current = true;
    const userMsg = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    const currentInput = input;
    setInput('');
    setLoading(true);

    try {
      const res = await axios.post(
        `${API_BASE}/api/chat`,
        { user_message: currentInput },
        { headers: authHeaders() },
      );
      // TOKEN_COUNTER: attach token usage to the bot message — remove when done testing
      setMessages(prev => [...prev, { role: 'bot', content: res.data.reply, tokens: res.data.tokens }]);
      if (res.data.tokens) {
        setSessionTokens(s => ({
          prompt: s.prompt + (res.data.tokens.prompt || 0),
          completion: s.completion + (res.data.tokens.completion || 0),
          total: s.total + (res.data.tokens.total || 0),
          calls: s.calls + 1,
        }));
      }
      if (res.data.new_reminder) fetchReminders();
    } catch (err) {
      if (handleAuthError(err)) return;
      const message = err.response?.data?.message || 'Something went wrong. Check the console.';
      setMessages(prev => [...prev, { role: 'bot', content: message }]);
    } finally {
      setLoading(false);
    }
  };

  const deleteReminder = async (id) => {
    try {
      await axios.delete(`${API_BASE}/api/reminders/${id}`, { headers: authHeaders() });
      fetchReminders();
    } catch (err) {
      handleAuthError(err);
    }
  };

  const clearAllHistory = async () => {
    if (!window.confirm('Wipe all chats and reminders for this account?')) return;
    try {
      await axios.post(`${API_BASE}/api/clear-all`, {}, { headers: authHeaders() });
      setMessages([]);
      setReminders([]);
      setHistoryReminders([]);
    } catch (err) {
      handleAuthError(err);
    }
  };

  const savePersona = async () => {
    setLoading(true);
    try {
      const res = await axios.put(`${API_BASE}/api/persona`, persona, { headers: authHeaders() });
      setPersona({
        persona_name: res.data.persona_name || '',
        behavior_profile: res.data.behavior_profile || '',
        system_instruction: res.data.system_instruction || '',
      });
      const updatedUser = { ...user, personaName: res.data.persona_name };
      setUser(updatedUser);
      localStorage.setItem('sidekick_user', JSON.stringify(updatedUser));
      setIsPersonaModalOpen(false);
    } catch (err) {
      if (!handleAuthError(err)) alert('Could not save persona.');
    } finally {
      setLoading(false);
    }
  };

  const compressPersona = async () => {
    const raw = persona.behavior_profile.trim();
    if (raw.length < 20) {
      alert('Paste a longer chat sample first — at least a few messages.');
      return;
    }
    if (!window.confirm('Compress the pasted chat into a compact style profile? This replaces the current text and saves tokens on every future message.')) return;
    setCompressing(true);
    try {
      const res = await axios.post(
        `${API_BASE}/api/persona/compress`,
        { raw_chat: raw },
        { headers: authHeaders() },
      );
      setPersona(p => ({ ...p, behavior_profile: res.data.compressed }));
      // TOKEN_COUNTER: remember the compression cost — remove when done testing
      if (res.data.tokens) setLastCompressTokens(res.data.tokens);
    } catch (err) {
      if (!handleAuthError(err)) {
        const msg = err.response?.data?.message || 'Compression failed. Try again in a moment.';
        alert(msg);
      }
    } finally {
      setCompressing(false);
    }
  };

  const logout = () => {
    clearSession();
    setUser(null);
    setMessages([]);
    setReminders([]);
    setAuthMode('login');
    setOnboardingForm({ username: '', personaName: '', password: '' });
    setAuthError('');
    setAuthNotice('');
  };

  if (!user) {
    return (
      <div className="h-screen w-screen bg-gradient-to-br from-blush-50 via-cream-50 to-purple-50 flex items-center justify-center p-6 font-sans">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-white/90 backdrop-blur p-8 rounded-3xl shadow-xl max-w-md w-full border border-blush-100"
        >
          <div className="text-center space-y-2 mb-8">
            <div className="inline-block p-4 bg-gradient-to-br from-blush-100 to-fuchsia-100 rounded-2xl text-blush-500 mb-2 shadow-sm">
              <Heart size={28} className="fill-blush-500 animate-heart-pulse" />
            </div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-blush-600 to-fuchsia-600 bg-clip-text text-transparent">Sidekick 💖</h1>
            <p className="text-sm text-slate-500">{authMode === 'register' ? 'Create an account to save your chats.' : 'Welcome back, jaan.'}</p>
          </div>

          <div className="flex bg-blush-50 p-1 rounded-xl mb-5">
            <button
              type="button"
              onClick={() => {
                setAuthMode('login');
                setAuthError('');
                setAuthNotice('');
                setOnboardingForm({ username: '', personaName: '', password: '' });
              }}
              className={`flex-1 py-2 text-xs font-semibold rounded-lg transition ${authMode === 'login' ? 'bg-white text-blush-600 shadow-sm' : 'text-slate-500'}`}
            >
              Sign in
            </button>
            <button
              type="button"
              onClick={() => {
                setAuthMode('register');
                setAuthError('');
                setAuthNotice('');
                setOnboardingForm({ username: '', personaName: '', password: '' });
              }}
              className={`flex-1 py-2 text-xs font-semibold rounded-lg transition ${authMode === 'register' ? 'bg-white text-blush-600 shadow-sm' : 'text-slate-500'}`}
            >
              Register
            </button>
          </div>

          <form onSubmit={handleOnboard} className="space-y-4">
            <Field label="Username">
              <input
                type="text" required maxLength={40}
                value={onboardingForm.username}
                onChange={e => setOnboardingForm({ ...onboardingForm, username: e.target.value })}
                className="field-input"
              />
            </Field>
            {authMode === 'register' && (
              <Field label="Persona name (optional)">
                <input
                  type="text" maxLength={40}
                  placeholder="e.g. Nova"
                  value={onboardingForm.personaName}
                  onChange={e => setOnboardingForm({ ...onboardingForm, personaName: e.target.value })}
                  className="field-input"
                />
              </Field>
            )}
            <Field label="Password">
              <input
                type="password" required minLength={8} maxLength={128}
                placeholder="at least 8 characters"
                value={onboardingForm.password}
                onChange={e => setOnboardingForm({ ...onboardingForm, password: e.target.value })}
                className="field-input"
              />
            </Field>
            {authError && <p className="text-sm text-red-500 text-center">{authError}</p>}
            {authNotice && <p className="text-sm text-emerald-600 text-center">{authNotice}</p>}
            <button
              type="submit" disabled={loading}
              className="w-full bg-gradient-to-r from-blush-500 to-fuchsia-500 hover:from-blush-600 hover:to-fuchsia-600 text-white font-semibold py-3.5 rounded-2xl shadow transition active:scale-[0.98] disabled:opacity-50"
            >
              {loading ? 'Loading…' : (authMode === 'register' ? 'Create account' : 'Sign in')}
            </button>
          </form>
        </motion.div>
        <style>{`.field-input{width:100%;padding:14px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;font-weight:500;color:#334155;outline:none}.field-input:focus{border-color:#ff7099;background:#fff}`}</style>
      </div>
    );
  }

  const listedReminders = viewMode === 'active' ? reminders : historyReminders;

  return (
    <>
      <div className="flex h-screen bg-slate-50 font-sans text-slate-900 overflow-hidden text-sm">
        <motion.aside
          initial={false}
          animate={{ width: isSidebarOpen ? 320 : 0, opacity: isSidebarOpen ? 1 : 0 }}
          className="bg-white/80 backdrop-blur border-r border-blush-100 flex flex-col shadow-sm z-20 relative overflow-hidden"
        >
          <div className="p-4 border-b border-blush-100 flex items-center justify-between min-w-[320px]">
            <div className="flex items-center gap-2 text-blush-600 font-semibold">
              <Bell size={16} />
              <span className="capitalize">{viewMode} tasks</span>
            </div>
            <div className="flex gap-1 bg-blush-50 p-1 rounded-lg">
              <button onClick={() => setViewMode('active')} className={`p-1.5 rounded-md ${viewMode === 'active' ? 'bg-white shadow-sm text-blush-600' : 'text-slate-400'}`}>
                <Clock size={14} />
              </button>
              <button onClick={() => setViewMode('history')} className={`p-1.5 rounded-md ${viewMode === 'history' ? 'bg-white shadow-sm text-blush-600' : 'text-slate-400'}`}>
                <History size={14} />
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-2 min-w-[320px]">
            <AnimatePresence mode="popLayout">
              {listedReminders.length === 0 ? (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-slate-400 text-xs text-center mt-12 italic">
                  {viewMode === 'active' ? 'No pending tasks' : 'No completed tasks'}
                </motion.div>
              ) : (
                listedReminders.map((r) => (
                  <motion.div
                    layout
                    initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 10 }}
                    key={r.id}
                    className={`p-3 rounded-xl border flex items-center gap-3 group ${viewMode === 'active' ? 'bg-blush-50/60 border-blush-100 hover:border-blush-300' : 'bg-emerald-50/40 border-emerald-100'}`}
                  >
                    <div className={`p-2 rounded-lg bg-white ${viewMode === 'active' ? 'text-blush-500' : 'text-emerald-500'}`}>
                      {viewMode === 'active' ? <Clock size={14} /> : <CheckCircle size={14} />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className={`font-medium truncate ${viewMode === 'active' ? 'text-slate-700' : 'text-slate-500 line-through'}`}>{r.task}</p>
                      <p className={`text-[11px] font-semibold uppercase tracking-wide ${viewMode === 'active' ? 'text-blush-500' : 'text-slate-400'}`}>
                        {viewMode === 'active' ? formatRemainingTime(r.due_at) : 'Completed'}
                      </p>
                    </div>
                    <button onClick={() => deleteReminder(r.id)} className="text-slate-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition">
                      <Trash2 size={14} />
                    </button>
                  </motion.div>
                ))
              )}
            </AnimatePresence>
          </div>

          <div className="p-4 border-t border-blush-100 min-w-[320px] bg-blush-50/40 space-y-2">
            <div className="flex items-center gap-2 mb-2 px-1">
              <div className="p-2 bg-white rounded-lg border border-blush-100 text-blush-400"><UserIcon size={14} /></div>
              <div className="flex-1 truncate">
                <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide">Logged in</p>
                <p className="text-sm font-semibold text-slate-700 truncate">{user.username}</p>
              </div>
              <button onClick={logout} className="text-xs font-semibold text-slate-500 hover:text-red-500 bg-white px-2 py-1 rounded-md border border-blush-100">
                Log out
              </button>
            </div>
            <button
              onClick={() => setIsPersonaModalOpen(true)}
              className="w-full flex items-center justify-center gap-2 py-2.5 text-xs font-semibold text-blush-600 bg-blush-100 hover:bg-blush-200 rounded-xl transition"
            >
              <Settings size={14} /> Persona settings
            </button>
            <button onClick={clearAllHistory} className="w-full flex items-center justify-center gap-2 py-2 text-xs font-semibold text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-xl transition">
              <Trash2 size={14} /> Clear all data
            </button>
          </div>
        </motion.aside>

        <div className="flex-1 flex flex-col relative min-w-0">
          <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="absolute left-4 top-20 z-30 p-1.5 bg-white rounded-full border border-blush-200 shadow-sm text-blush-400 hover:text-blush-600 transition">
            {isSidebarOpen ? <ChevronLeft size={14} /> : <ChevronRight size={14} />}
          </button>

          <header className="bg-white/70 backdrop-blur border-b border-blush-100 p-4 flex items-center gap-3">
            <div className="bg-gradient-to-br from-blush-500 to-fuchsia-500 p-2 rounded-xl shadow-sm">
              <Heart className="text-white fill-white" size={16} />
            </div>
            <h1 className="font-semibold text-blush-900 flex-1 truncate">{user.personaName}</h1>
            {/* TOKEN_COUNTER: session-wide token totals — remove when done testing */}
            <div className="text-[10px] font-mono text-slate-500 bg-blush-50 px-3 py-1.5 rounded-lg border border-blush-200" title="Session token totals">
              <span className="font-bold text-slate-700">{sessionTokens.total.toLocaleString()}</span> tok
              <span className="text-slate-300 mx-1.5">•</span>
              in {sessionTokens.prompt.toLocaleString()}
              <span className="text-slate-300 mx-1.5">•</span>
              out {sessionTokens.completion.toLocaleString()}
              <span className="text-slate-300 mx-1.5">•</span>
              {sessionTokens.calls} msg
            </div>
          </header>

          <main ref={mainRef} onScroll={handleMainScroll} className="flex-1 overflow-y-auto p-6 space-y-5">
            <AnimatePresence>
              {messages.length === 0 && !loading && (
                <div className="h-full flex flex-col items-center justify-center text-center space-y-3 max-w-sm mx-auto pt-24">
                  <div className="p-5 bg-gradient-to-br from-blush-100 to-fuchsia-100 rounded-full text-blush-500 shadow-sm">
                    <Heart size={32} className="fill-blush-500 animate-heart-pulse" />
                  </div>
                  <h2 className="text-lg font-semibold text-blush-900">missed u, {user.username} 💕</h2>
                  <p className="text-sm text-slate-500">Tip: open <span className="font-semibold text-blush-600">Persona settings</span> to paste real chat samples for the bot to mirror.</p>
                </div>
              )}
              {messages.map((msg, idx) => (
                <motion.div
                  initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}
                  key={idx}
                  className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
                >
                  <div className={`p-3.5 rounded-2xl max-w-[80%] shadow-sm ${msg.role === 'user' ? 'bg-gradient-to-br from-blush-500 to-fuchsia-500 text-white rounded-tr-sm' : 'bg-white/90 text-slate-800 rounded-tl-sm border border-blush-100'}`}>
                    <div className="prose prose-sm max-w-none text-inherit break-words leading-relaxed">
                      <ReactMarkdown>{msg.content || '…'}</ReactMarkdown>
                    </div>
                  </div>
                  {/* TOKEN_COUNTER: per-message token breakdown — remove when done testing */}
                  {msg.role === 'bot' && msg.tokens && (
                    <div className="text-[10px] font-mono text-slate-400 mt-1 ml-1">
                      in {msg.tokens.prompt} · out {msg.tokens.completion} · total {msg.tokens.total}
                    </div>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>
            {loading && (
              <div className="flex justify-start">
                <div className="bg-white p-3 px-4 rounded-2xl border border-blush-100 flex gap-1 shadow-sm">
                  <span className="w-1.5 h-1.5 bg-blush-400 rounded-full animate-bounce"></span>
                  <span className="w-1.5 h-1.5 bg-blush-400 rounded-full animate-bounce [animation-delay:0.15s]"></span>
                  <span className="w-1.5 h-1.5 bg-blush-400 rounded-full animate-bounce [animation-delay:0.3s]"></span>
                </div>
              </div>
            )}
            <div ref={scrollRef} />
          </main>

          <footer className="p-4 bg-white/70 backdrop-blur border-t border-blush-100">
            <form onSubmit={sendMessage} className="max-w-4xl mx-auto flex gap-2 bg-white p-2 rounded-2xl border border-blush-200 shadow-sm focus-within:border-blush-400">
              <input
                type="text" value={input} onChange={e => setInput(e.target.value)}
                placeholder={`Message ${user.personaName}…`} maxLength={4000}
                className="flex-1 bg-transparent p-2 pl-3 focus:outline-none text-slate-700 placeholder:text-slate-400"
              />
              <button type="submit" disabled={!input.trim() || loading} className="bg-gradient-to-br from-blush-500 to-fuchsia-500 hover:from-blush-600 hover:to-fuchsia-600 text-white p-2.5 rounded-xl shadow-sm transition disabled:opacity-40">
                {loading ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Send size={16} />}
              </button>
            </form>
          </footer>
        </div>
      </div>

      <AnimatePresence>
        {isPersonaModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              onClick={() => setIsPersonaModalOpen(false)}
              className="absolute inset-0 bg-blush-900/30 backdrop-blur-sm"
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              className="bg-white rounded-3xl shadow-2xl w-full max-w-xl overflow-hidden relative border border-blush-100 z-10"
            >
              <div className="p-7 space-y-5 max-h-[85vh] overflow-y-auto">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2.5 bg-gradient-to-br from-blush-100 to-fuchsia-100 rounded-xl text-blush-500"><Heart size={20} className="fill-blush-500" /></div>
                    <div>
                      <h2 className="text-lg font-bold text-blush-900">Persona settings</h2>
                      <p className="text-xs text-slate-500">Shape your sidekick's voice & vibe 💕</p>
                    </div>
                  </div>
                  <button onClick={() => setIsPersonaModalOpen(false)} className="p-2 hover:bg-blush-50 rounded-full">
                    <X size={18} className="text-slate-400" />
                  </button>
                </div>

                <Field label="Persona name">
                  <input
                    type="text" maxLength={40}
                    value={persona.persona_name}
                    onChange={e => setPersona({ ...persona, persona_name: e.target.value })}
                    className="field-input"
                    placeholder="Who the bot is pretending to be"
                  />
                </Field>

                <Field label={`Behavior samples (${persona.behavior_profile.length}/50000)`}>
                  <textarea
                    value={persona.behavior_profile}
                    onChange={e => setPersona({ ...persona, behavior_profile: e.target.value.slice(0, 50000) })}
                    placeholder="Paste real chat messages from the person you want the bot to mimic. Raw WhatsApp exports work — timestamps and the other speaker's lines will be ignored by the compressor."
                    className="field-input h-48 resize-none font-mono text-xs leading-relaxed"
                  />
                  <button
                    type="button"
                    onClick={compressPersona}
                    disabled={compressing || persona.behavior_profile.trim().length < 20}
                    className="w-full mt-2 flex items-center justify-center gap-2 py-2.5 text-xs font-semibold text-blush-600 bg-blush-100 hover:bg-blush-200 rounded-xl transition disabled:opacity-50"
                  >
                    <Wand2 size={14} />
                    {compressing ? 'Compressing…' : 'Compress with AI (saves tokens, keeps realism)'}
                  </button>
                  {/* TOKEN_COUNTER: last compression cost — remove when done testing */}
                  {lastCompressTokens && (
                    <div className="text-[10px] font-mono text-slate-400 mt-2 px-1">
                      Last compression: in {lastCompressTokens.prompt} · out {lastCompressTokens.completion} · total {lastCompressTokens.total} tokens
                    </div>
                  )}
                  <p className="text-[10px] text-slate-400 leading-relaxed px-1 pt-1">
                    Click after pasting raw chat. One-time AI call distills the voice into a compact style card + representative messages — every future chat becomes much cheaper without losing authenticity.
                  </p>
                </Field>

                <Field label={`System instruction (${persona.system_instruction.length}/4000)`}>
                  <textarea
                    value={persona.system_instruction}
                    onChange={e => setPersona({ ...persona, system_instruction: e.target.value.slice(0, 4000) })}
                    placeholder="Extra instructions layered on top of the voice — e.g. 'respond in Roman Urdu', 'stay playful but never crude', 'act jealous if I mention other people'."
                    className="field-input h-28 resize-none text-sm leading-relaxed"
                  />
                </Field>

                <div className="flex gap-3 pt-2">
                  <button
                    onClick={() => setPersona({ ...persona, behavior_profile: '', system_instruction: '' })}
                    className="flex-1 py-3 text-xs font-semibold text-slate-600 bg-blush-50 hover:bg-blush-100 rounded-xl transition"
                  >
                    Clear behavior + instruction
                  </button>
                  <button
                    onClick={savePersona} disabled={loading}
                    className="flex-[2] py-3 bg-gradient-to-r from-blush-500 to-fuchsia-500 hover:from-blush-600 hover:to-fuchsia-600 text-white font-semibold rounded-xl shadow transition active:scale-[0.98] disabled:opacity-50"
                  >
                    {loading ? 'Saving…' : 'Save persona'}
                  </button>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {activeNotification && (
          <motion.div
            initial={{ opacity: 0, y: -30 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="fixed top-6 left-1/2 -translate-x-1/2 z-[100] w-[90%] max-w-sm"
          >
            <div className="bg-gradient-to-r from-blush-500 to-fuchsia-500 p-4 rounded-2xl shadow-2xl flex items-center gap-3 text-white">
              <div className="p-2 bg-white/20 rounded-lg"><Bell className="animate-pulse" size={20} /></div>
              <div className="flex-1 min-w-0">
                <p className="text-[10px] font-bold uppercase tracking-wider opacity-80">Reminder</p>
                <p className="text-sm font-semibold truncate">{activeNotification}</p>
              </div>
              <button onClick={() => setActiveNotification(null)} className="p-1 hover:bg-white/10 rounded-full">
                <X size={16} />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <style>{`.field-input{width:100%;padding:12px 14px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;font-weight:500;color:#334155;outline:none;transition:all .15s}.field-input:focus{border-color:#ff7099;background:#fff}`}</style>
    </>
  );
}

function Field({ label, children }) {
  return (
    <div className="space-y-1.5">
      <label className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider px-1">{label}</label>
      {children}
    </div>
  );
}

export default App;
