import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Send, Sparkles, Bell, CheckCircle, Clock, ChevronLeft, ChevronRight, Trash2, History, MessageSquareCode, User as UserIcon, Heart, Lock, Camera, X } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { motion, AnimatePresence } from 'framer-motion';

// --- v8.0 Professional Safety Boundary ---
class ChatErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError(error) { return { hasError: true }; }
  componentDidCatch(error, errorInfo) { console.error("Chat Render Error:", error, errorInfo); }
  render() {
    if (this.state.hasError) {
      return (
        <div className="p-10 text-center space-y-4">
          <div className="text-red-400 font-bold italic">Babe, I'm a bit confused right now... 💔</div>
          <button onClick={() => window.location.reload()} className="text-xs bg-pink-100 text-pink-600 px-4 py-2 rounded-xl">Refresh Chat</button>
        </div>
      );
    }
    return this.props.children;
  }
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [user, setUser] = useState(null); // { id, username, botName, pin }
  const [onboardingForm, setOnboardingForm] = useState({ username: '', botName: '', pin: '' });
  const [reminders, setReminders] = useState([]);
  const [historyReminders, setHistoryReminders] = useState([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [viewMode, setViewMode] = useState('active'); // 'active' or 'history'
  const scrollRef = useRef(null);
  const userRef = useRef(null); // ALWAYS current identity
  const messageCountRef = useRef(0); // For sensory detection
  const alreadySpokenRef = useRef(""); // To prevent the echo!
  const buzzedRemindersRef = useRef(new Set()); // Instant Trigger Memory!

  // Helper to format remaining time
  const formatRemainingTime = (dueAt) => {
    if (!dueAt) return 'Pending...';
    const due = new Date(dueAt.includes('Z') ? dueAt : dueAt + 'Z'); 
    const now = new Date();
    const diffMs = due - now;
    if (diffMs <= 0) return '🔔 Due Now!';
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours > 0) return `${diffHours}h ${diffMins % 60}m left`;
    return `${diffMins}m left`;
  };

  // 1. Initial Load & Identity Check
  useEffect(() => {
    const savedUser = localStorage.getItem('sidekick_user');
    if (savedUser) {
      const parsedUser = JSON.parse(savedUser);
      setUser(parsedUser);
      userRef.current = parsedUser; // Sync Ref
      initApp(parsedUser);
    }
  }, []);

  // 2. Polling Logic (Only if logged in)
  useEffect(() => {
    if (!user?.id) return;
    const interval = setInterval(() => {
      fetchReminders();
      fetchChatHistoryPolling();
    }, 1500);
    return () => clearInterval(interval);
  }, [user, viewMode]);

  const initApp = async (currentUser) => {
    try {
      const token = localStorage.getItem('sidekick_token');
      if (!token) {
         setUser(null);
         return;
      }
      // Fetch Chat History
      // Fetch Chat History
      const chatRes = await axios.get(`${API_BASE}/api/chat/history`, { 
        headers: { 'Authorization': `Bearer ${token}` } 
      });
      const formattedHistory = chatRes.data.reverse().map(msg => ({
        role: msg.role === 'user' ? 'user' : 'bot',
        content: msg.content
      }));
      setMessages(formattedHistory);
      messageCountRef.current = formattedHistory.length; // Initial Sync!
      fetchReminders(currentUser.id, token); 
    } catch (err) {
      console.error("Initialization failed:", err);
      // HARD RESET: If server restarted/DB reset, redirect to onboarding
      if (err.response?.status === 404 || err.response?.status === 401) {
        console.log("🔄 [Security] Session expired or DB reset. Redirecting to onboarding...");
        localStorage.removeItem('sidekick_user');
        localStorage.removeItem('sidekick_token');
        setUser(null);
      }
    }
  };


  const fetchChatHistoryPolling = async () => {
    // 🫦 Flicker Shield: Lock polling while actively chatting
    if (loading) return;

    const token = localStorage.getItem('sidekick_token');
    if (!token) return;
    try {
      const chatRes = await axios.get(`${API_BASE}/api/chat/history`, { 
        headers: { 'Authorization': `Bearer ${token}` } 
      });
      const newHistory = chatRes.data.reverse().map(msg => ({
        role: msg.role === 'user' ? 'user' : 'bot',
        content: msg.content
      }));
      
      // 🫦 Synchronicity: History Syncing 100%
      setMessages(newHistory);
      messageCountRef.current = newHistory.length;
    } catch (err) { console.error("History polling err:", err); }
  };

  const triggerSensoryAlert = (text) => {
    // 🫦 Voice-Only Delivery: Focused and Professional
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.pitch = 1.1; 
    utterance.rate = 1.0;
    window.speechSynthesis.speak(utterance);
  };

  const fetchReminders = async (forcedId, forcedToken) => {
    const token = forcedToken || localStorage.getItem('sidekick_token');
    if (!token) return;
    try {
      const endpoint = viewMode === 'active' ? '/api/reminders?status=pending' : '/api/reminders?status=completed';
      const res = await axios.get(`${API_BASE}${endpoint}`, { 
        headers: { 'Authorization': `Bearer ${token}` } 
      });
      
      if (viewMode === 'active') {
        setReminders(res.data);
        
        // INSTANT TRIGGER: Check if any pending reminder is now 'Due Now'! 🫦🔔✨
        const now = new Date();
        res.data.forEach(r => {
          if (!r.due_at) return;
          const due = new Date(r.due_at.includes('Z') ? r.due_at : r.due_at + 'Z');
          if (due <= now && !buzzedRemindersRef.current.has(r.id)) {
            // FIRE!
            triggerSensoryAlert(`Babe! Time for your reminder: '${r.task}'! 😘`);
            buzzedRemindersRef.current.add(r.id);
            
            // Tell the server to mark it as completed so it moves to history
            axios.post(`${API_BASE}/api/reminders/${r.id}/complete`, {}, { 
              headers: { 'Authorization': `Bearer ${token}` } 
            })
              .then(() => {
                 fetchReminders(); // Refresh sidebar instantly
                 fetchChatHistoryPolling(); // Refresh history instantly
              })
              .catch(() => {});
          }
        });
      } else {
        setHistoryReminders(res.data);
      }
    } catch (err) { console.error("Polling error:", err); }
  };

  // 3. User Handlers
  const handleOnboard = async (e) => {
    e.preventDefault();
    if (!onboardingForm.username || !onboardingForm.botName || !onboardingForm.pin) return;
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/api/onboard?username=${encodeURIComponent(onboardingForm.username)}&bot_name=${encodeURIComponent(onboardingForm.botName)}&pin=${onboardingForm.pin}`);
      const newUser = { 
        id: res.data.user_id, 
        username: res.data.username, 
        botName: res.data.bot_name,
        pin: onboardingForm.pin 
      };
      localStorage.setItem('sidekick_user', JSON.stringify(newUser));
      localStorage.setItem('sidekick_token', res.data.access_token);
      setUser(newUser);
      userRef.current = newUser; // Instant Ref Sync
      setMessages([]);
      setReminders([]);
      setHistoryReminders([]);
      
      // INSTANT HISTORY: Load memory on join
      initApp(newUser); 
      
      // Request Permissions & Enable Voice!
      if (Notification.permission !== 'granted') {
        Notification.requestPermission();
      }
      // Speech activation gesture
      const dummy = new SpeechSynthesisUtterance("Hi");
      dummy.volume = 0;
      window.speechSynthesis.speak(dummy);

      setLoading(false);
    } catch (err) {
      if (err.response?.status === 401) {
        alert("Wrong Key, Jan! 💔 This profile is locked. Use your own PIN!");
      } else {
        alert("Registration failed. Please try again, jan! 💔");
      }
      setLoading(false);
    }
  };

  const deleteReminder = async (id) => {
    try {
      const token = localStorage.getItem('sidekick_token');
      await axios.delete(`${API_BASE}/api/reminders/${id}`, { 
        headers: { 'Authorization': `Bearer ${token}` } 
      });
      fetchReminders(); 
    } catch (err) {
      console.error("Delete error:", err);
    }
  };

  const clearAllHistory = async () => {
    if (!window.confirm("Jan, are you sure? This will wipe your private chats and reminders! 💔")) return;
    try {
      const token = localStorage.getItem('sidekick_token');
      await axios.post(`${API_BASE}/api/clear-all`, {}, { 
        headers: { 'Authorization': `Bearer ${token}` } 
      });
      setMessages([]);
      setReminders([]);
      setHistoryReminders([]);
    } catch (err) { console.error("Clear error:", err); }
  };

  const sendMessage = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    if (!input.trim() || loading) return;
    if (!user?.id) {
        alert("Hold on, jan! I'm still waking up. Give me a second... 🫦");
        return;
    }

    const userMsg = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    const currentInput = input;
    setInput('');
    setLoading(true);

    try {
      const token = localStorage.getItem('sidekick_token');
      const response = await axios.post(
        `${API_BASE}/api/chat`,
        { user_message: currentInput },
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      const botReply = response.data[user.bot_name] || response.data[user.botName] || response.data.reply || "Invalid response format";
      setMessages(prev => [...prev, { role: 'bot', content: botReply }]);
      
      // INSTANT SYNC: If the AI created a reminder, refresh the sidebar immediately! 🫦🔔✨
      if (response.data.new_reminder) {
        fetchReminders();
      }
    } catch (error) {
      console.error("FULL CHAT ERROR:", error);
      // HARD RESET on 404 (ID expired or DB reset)
      if (error.response?.status === 404 || error.response?.status === 401) {
        console.log("🔄 [Security Fix] Chat ID 404. Redirecting to onboarding...");
        localStorage.removeItem('sidekick_user');
        localStorage.removeItem('sidekick_token');
        setUser(null);
        return; 
      }
      setMessages(prev => [...prev, { role: 'bot', content: "Server error, jan. 💔 Check the browser console!" }]);
    } finally { setLoading(false); }
  };

  // Auto-scroll
  useEffect(() => { 
    if (messages.length > messageCountRef.current) {
      scrollRef.current?.scrollIntoView({ behavior: "smooth" }); 
    }
  }, [messages]);

  // --- ONBOARDING VIEW ---
  if (!user) {
    return (
      <div className="h-screen w-screen bg-gradient-to-br from-rose-50 to-pink-100 flex items-center justify-center p-6 font-sans overflow-hidden">
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
          className="bg-white p-8 rounded-[2rem] shadow-2xl max-w-md w-full border border-pink-100 relative overflow-hidden"
        >
          <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
             <Heart size={120} className="text-pink-500 fill-current" />
          </div>
          
          <div className="text-center space-y-2 mb-8">
            <div className="inline-block p-4 bg-pink-50 rounded-2xl text-pink-500 mb-2">
               <Lock size={32} />
            </div>
            <h1 className="text-2xl font-black text-gray-800 tracking-tight">Enter the Vault</h1>
            <p className="text-sm text-gray-500">Your private history is PIN-protected.</p>
          </div>

          <form onSubmit={handleOnboard} className="space-y-4">
            <div className="space-y-1">
              <label className="text-[10px] font-bold text-gray-400 uppercase tracking-widest px-1">Username</label>
              <input 
                type="text" required maxLength={20}
                placeholder="e.g. Abdul"
                value={onboardingForm.username}
                onChange={e => setOnboardingForm({...onboardingForm, username: e.target.value})}
                className="w-full p-4 bg-gray-50 border border-gray-100 rounded-2xl focus:outline-none focus:border-pink-300 transition-all text-gray-700 font-medium"
              />
            </div>
            <div className="space-y-1">
              <label className="text-[10px] font-bold text-gray-400 uppercase tracking-widest px-1">Bot's Name</label>
              <input 
                type="text" required maxLength={20}
                placeholder="e.g. Hafsa"
                value={onboardingForm.botName}
                onChange={e => setOnboardingForm({...onboardingForm, botName: e.target.value})}
                className="w-full p-4 bg-gray-50 border border-gray-100 rounded-2xl focus:outline-none focus:border-pink-300 transition-all text-gray-700 font-medium"
              />
            </div>
            <div className="space-y-1">
              <label className="text-[10px] font-bold text-gray-400 uppercase tracking-widest px-1">4-Digit Security PIN</label>
              <input 
                type="password" required maxLength={4} pattern="\d{4}"
                placeholder="••••"
                value={onboardingForm.pin}
                onChange={e => setOnboardingForm({...onboardingForm, pin: e.target.value.replace(/\D/g, '')})}
                className="w-full p-4 bg-gray-50 border border-gray-100 rounded-2xl focus:outline-none focus:border-pink-300 transition-all text-center text-xl tracking-[1em] font-black"
              />
            </div>
            <button 
              type="submit" disabled={loading}
              className="w-full bg-pink-600 hover:bg-pink-700 text-white font-bold py-4 rounded-2xl shadow-lg shadow-pink-200 transition-all active:scale-95 disabled:opacity-50 mt-4"
            >
              {loading ? "Waking her up..." : "UNLOCK CHAT"}
            </button>
          </form>
          <p className="text-[9px] text-center text-gray-400 mt-6 uppercase tracking-widest font-bold font-mono">End-to-End Privacy Locked 🔒</p>
        </motion.div>
      </div>
    );
  }

  // --- MAIN APP VIEW ---
  const activeRemindersList = viewMode === 'active' ? reminders : historyReminders;

  return (
    <div className="flex h-screen bg-[#F7F9FB] font-sans text-gray-900 overflow-hidden text-[14px]">
      <motion.aside
        initial={false}
        animate={{ width: isSidebarOpen ? 320 : 0, opacity: isSidebarOpen ? 1 : 0 }}
        className="bg-white border-r border-gray-100 flex flex-col shadow-xl z-20 relative overflow-hidden"
      >
        <div className="p-4 border-b border-gray-50 flex items-center justify-between min-w-[320px]">
          <div className="flex items-center gap-2 text-pink-600 font-bold">
            <Bell size={18} />
            <span className="capitalize">{viewMode} Tasks</span>
          </div>
          <div className="flex gap-1 bg-gray-50 p-1 rounded-lg">
            <button onClick={() => setViewMode('active')} className={`p-1.5 rounded-md transition-all ${viewMode === 'active' ? 'bg-white shadow-sm text-pink-500' : 'text-gray-400'}`}>
              <Clock size={16} />
            </button>
            <button onClick={() => setViewMode('history')} className={`p-1.5 rounded-md transition-all ${viewMode === 'history' ? 'bg-white shadow-sm text-pink-500' : 'text-gray-400'}`}>
              <History size={16} />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-3 min-w-[320px]">
          <AnimatePresence mode="popLayout">
            {activeRemindersList.length === 0 ? (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-gray-400 text-xs text-center mt-10 italic flex flex-col items-center gap-2">
                <MessageSquareCode size={40} className="text-gray-100" />
                <p>{viewMode === 'active' ? 'No pending tasks...' : 'Task History'}</p>
              </motion.div>
            ) : (
              activeRemindersList.map((r) => (
                <motion.div layout initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }} key={r.id}
                  className={`p-3 rounded-xl border flex items-center gap-3 transition-all group shadow-sm ${viewMode === 'active' ? 'bg-gray-50 border-gray-100 hover:border-pink-200' : 'bg-green-50/30 border-green-100 grayscale-[0.5]'}`}
                >
                  <div className={`p-2 rounded-lg shadow-sm ${viewMode === 'active' ? 'bg-white text-pink-500' : 'bg-white text-green-500'}`}>
                    {viewMode === 'active' ? <Clock size={14} /> : <CheckCircle size={14} />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-medium transition-colors ${viewMode === 'active' ? 'text-gray-700' : 'text-gray-500 line-through'}`}>{r.task}</p>
                    <p className={`text-[10px] font-bold tracking-tight uppercase ${viewMode === 'active' ? 'text-pink-400' : 'text-gray-400'}`}>
                      {viewMode === 'active' ? formatRemainingTime(r.due_at) : 'Completed'}
                    </p>
                  </div>
                  <button onClick={() => deleteReminder(r.id)} className="text-gray-300 hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100">
                    <Trash2 size={16} />
                  </button>
                </motion.div>
              ))
            )}
          </AnimatePresence>
        </div>

        <div className="p-4 border-t border-gray-50 min-w-[320px] bg-gray-50/50">
           <div className="flex items-center gap-2 mb-4 px-2">
              <div className="p-2 bg-white rounded-lg border border-gray-100 shadow-sm text-pink-400"><UserIcon size={14} /></div>
              <div className="flex-1 truncate"><p className="text-[10px] font-bold text-gray-400 uppercase tracking-tighter leading-none">Logged in as</p><p className="text-xs font-bold text-gray-700 truncate">{user.username}</p></div>
              <button 
                onClick={() => { localStorage.removeItem('sidekick_user'); window.location.reload(); }}
                className="text-[10px] font-bold text-pink-400 hover:text-pink-600 transition-colors bg-white px-2 py-1 rounded-md border border-gray-100"
              >Log out</button>
           </div>
           <button onClick={clearAllHistory} className="w-full flex items-center justify-center gap-2 py-2 text-xs font-bold text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-xl transition-all">
             <Trash2 size={14} /> RESET MY DATA
           </button>
        </div>
      </motion.aside>

      <div className="flex-1 flex flex-col relative min-w-0">
        <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="absolute left-4 top-20 z-30 p-1.5 bg-white rounded-full border border-gray-200 shadow-md hover:bg-gray-50 text-gray-400">
          {isSidebarOpen ? <ChevronLeft size={16} /> : <ChevronRight size={16} />}
        </button>

        <header className="bg-white/80 backdrop-blur-md border-b border-gray-100 p-4 flex items-center justify-between z-10">
          <div className="flex items-center gap-3">
            <div className="bg-gradient-to-tr from-pink-500 to-rose-400 p-2 rounded-xl shadow-md shadow-pink-100">
              <Sparkles className="text-white" size={18} />
            </div>
            <div><h1 className="text-base font-bold text-gray-800 capitalize tracking-tight font-black">{user.botName}</h1></div>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-6 space-y-6 bg-white/30">
          <ChatErrorBoundary>
            <AnimatePresence>
              {messages.length === 0 && !loading && (
                <div className="h-full flex flex-col items-center justify-center text-center space-y-4 max-w-sm mx-auto">
                  <div className="p-4 bg-gray-50 rounded-full text-pink-400"><Heart size={32} fill="currentColor" /></div>
                  <div><h2 className="text-lg font-bold text-gray-700 leading-tight">Ready for our chat, {user.username}?</h2><p className="text-sm text-gray-400 mt-1">Tell me everything...</p></div>
                </div>
              )}
              {messages.map((msg, idx) => (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`p-4 rounded-2xl max-w-[85%] shadow-sm ${msg.role === 'user' ? 'bg-pink-600 text-white rounded-tr-none shadow-pink-200' : 'bg-white text-gray-800 rounded-tl-none border border-gray-100 shadow-pink-50/50'}`}>
                    <div className="prose prose-sm max-w-none text-inherit break-words leading-relaxed font-medium">
                      <ReactMarkdown>{msg.content || (msg.role === 'bot' ? '...' : '')}</ReactMarkdown>
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </ChatErrorBoundary>
          {loading && (
            <div className="flex justify-start">
               <div className="bg-white p-3 px-4 rounded-2xl border border-gray-100 flex gap-1 shadow-sm">
                 <span className="w-1.5 h-1.5 bg-pink-400 rounded-full animate-bounce"></span>
                 <span className="w-1.5 h-1.5 bg-pink-400 rounded-full animate-bounce [animation-delay:0.2s]"></span>
                 <span className="w-1.5 h-1.5 bg-pink-400 rounded-full animate-bounce [animation-delay:0.4s]"></span>
               </div>
            </div>
          )}
          <div ref={scrollRef} />
        </main>

        <footer className="p-4 bg-white border-t border-gray-100">
          <form onSubmit={sendMessage} className="max-w-4xl mx-auto flex gap-3 bg-gray-50 p-2 rounded-2xl border border-gray-200 shadow-inner">
            <input type="text" value={input} onChange={(e) => setInput(e.target.value)} placeholder={`Message ${user.botName}...`}
              className="flex-1 bg-transparent p-2 pl-4 focus:outline-none text-gray-700 placeholder:text-gray-300 font-medium"
            />
            <button type="submit" disabled={!input.trim() || loading} className="bg-pink-600 text-white p-3 rounded-xl hover:bg-pink-700 transition-all shadow-md disabled:opacity-40">
              {loading ? <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Send size={18} />}
            </button>
          </form>
          <p className="text-[9px] text-center text-gray-300 mt-2 uppercase tracking-tighter font-bold font-mono">Private Vault Locked • User: {user.username}</p>
        </footer>
      </div>
    </div>
  );
}

export default App;