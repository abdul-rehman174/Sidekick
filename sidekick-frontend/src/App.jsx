import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Send, Sparkles, Bell, CheckCircle, Clock, ChevronLeft, ChevronRight, Trash2, History, MessageSquareCode } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [botName, setBotName] = useState('Assistant');
  const [reminders, setReminders] = useState([]);
  const [historyReminders, setHistoryReminders] = useState([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [viewMode, setViewMode] = useState('active'); // 'active' or 'history'
  const scrollRef = useRef(null);

  // Helper to format remaining time
  const formatRemainingTime = (dueAt) => {
    if (!dueAt) return 'Pending...';
    
    // Parse UTC date from server (Python sends UTC by default)
    const due = new Date(dueAt + 'Z'); 
    const now = new Date();
    const diffMs = due - now;
    
    if (diffMs <= 0) return '🔔 Due Now!';
    
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    
    if (diffHours > 0) {
      return `${diffHours}h ${diffMins % 60}m left`;
    }
    return `${diffMins}m left`;
  };

  // 1. Initial Load & Polling Logic
  useEffect(() => {
    const initApp = async () => {
      try {
        const configRes = await axios.get(`${API_BASE}/api/config`);
        setBotName(configRes.data.bot_name);
        
        // Fetch Chat History
        const chatRes = await axios.get(`${API_BASE}/api/chat/history`);
        const formattedHistory = chatRes.data.reverse().map(msg => ({
          role: msg.role === 'user' ? 'user' : 'bot',
          content: msg.content
        }));
        setMessages(formattedHistory);

        fetchReminders(); 
      } catch (err) {
        console.error("Initialization failed:", err);
      }
    };
    initApp();

    const interval = setInterval(() => {
      fetchReminders();
    }, 5000);

    return () => clearInterval(interval); 
  }, []);

  useEffect(() => {
    fetchReminders(); // Re-fetch when switching tabs
  }, [viewMode]);

  // 2. Auto-scroll
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // 3. API Handlers
  const fetchReminders = async () => {
    try {
      const endpoint = viewMode === 'active' ? '/api/reminders?status=pending' : '/api/reminders?status=completed';
      const res = await axios.get(`${API_BASE}${endpoint}`);
      if (viewMode === 'active') {
        setReminders(res.data);
      } else {
        setHistoryReminders(res.data);
      }
    } catch (err) {
      console.error("Polling error:", err);
    }
  };

  const deleteReminder = async (id) => {
    try {
      await axios.delete(`${API_BASE}/api/reminders/${id}`);
      fetchReminders(); 
    } catch (err) {
      console.error("Delete error:", err);
    }
  };

  const clearAllHistory = async () => {
    if (!window.confirm("Jan, are you sure? This will wipe all our chats and reminders forever! 💔")) return;
    
    try {
      await axios.post(`${API_BASE}/api/clear-all`);
      setMessages([]);
      setReminders([]);
      setHistoryReminders([]);
      alert("Everything's clean now! Starting fresh. ✨");
    } catch (err) {
      console.error("Clear error:", err);
    }
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    const currentInput = input;
    setInput('');
    setLoading(true);

    try {
      const response = await axios.post(
        `${API_BASE}/api/chat?user_message=${encodeURIComponent(currentInput)}`
      );

      const botReply = response.data[botName] || Object.values(response.data)[0];
      setMessages(prev => [...prev, { role: 'bot', content: botReply }]);

      setTimeout(fetchReminders, 500);
    } catch (error) {
      setMessages(prev => [...prev, { role: 'bot', content: "Server error, jan. 💔" }]);
    } finally {
      setLoading(false);
    }
  };

  const activeRemindersList = viewMode === 'active' ? reminders : historyReminders;

  return (
    <div className="flex h-screen bg-[#F7F9FB] font-sans text-gray-900 overflow-hidden text-[14px]">

      {/* --- SIDEBAR --- */}
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
            <button 
              onClick={() => setViewMode('active')}
              className={`p-1.5 rounded-md transition-all ${viewMode === 'active' ? 'bg-white shadow-sm text-pink-500' : 'text-gray-400'}`}
              title="Active Tasks"
            >
              <Clock size={16} />
            </button>
            <button 
              onClick={() => setViewMode('history')}
              className={`p-1.5 rounded-md transition-all ${viewMode === 'history' ? 'bg-white shadow-sm text-pink-500' : 'text-gray-400'}`}
              title="Task History"
            >
              <History size={16} />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-3 min-w-[320px]">
          <AnimatePresence mode="popLayout">
            {activeRemindersList.length === 0 ? (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-gray-400 text-xs text-center mt-10 italic flex flex-col items-center gap-2">
                <MessageSquareCode size={40} className="text-gray-100" />
                <p>{viewMode === 'active' ? 'No pending tasks...' : 'History is empty (last 7 days)'}</p>
              </motion.div>
            ) : (
              activeRemindersList.map((r) => (
                <motion.div
                  layout
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  key={r.id}
                  className={`p-3 rounded-xl border flex items-center gap-3 transition-all group shadow-sm ${
                    viewMode === 'active' ? 'bg-gray-50 border-gray-100 hover:border-pink-200' : 'bg-green-50/30 border-green-100 grayscale-[0.5]'
                  }`}
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
                  <button
                    onClick={() => deleteReminder(r.id)}
                    className="text-gray-300 hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100"
                    title="Remove permanently"
                  >
                    <Trash2 size={16} />
                  </button>
                </motion.div>
              ))
            )}
          </AnimatePresence>
        </div>

        {/* Clear All Footer */}
        <div className="p-4 border-t border-gray-50 min-w-[320px]">
           <button 
             onClick={clearAllHistory}
             className="w-full flex items-center justify-center gap-2 py-2 text-xs font-bold text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-xl transition-all"
           >
             <Trash2 size={14} />
             RESET SYSTEM
           </button>
        </div>
      </motion.aside>

      {/* --- MAIN CONTENT --- */}
      <div className="flex-1 flex flex-col relative min-w-0">

        {/* Toggle Drawer Button */}
        <button
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          className="absolute left-4 top-20 z-30 p-1.5 bg-white rounded-full border border-gray-200 shadow-md hover:bg-gray-50 text-gray-400"
        >
          {isSidebarOpen ? <ChevronLeft size={16} /> : <ChevronRight size={16} />}
        </button>

        <header className="bg-white/80 backdrop-blur-md border-b border-gray-100 p-4 flex items-center justify-between z-10">
          <div className="flex items-center gap-3">
            <div className="bg-gradient-to-tr from-pink-500 to-rose-400 p-2 rounded-xl shadow-md shadow-pink-100">
              <Sparkles className="text-white" size={18} />
            </div>
            <div>
              <h1 className="text-base font-bold text-gray-800 capitalize">{botName}</h1>
            </div>
          </div>
        </header>

        {/* Chat Feed */}
        <main className="flex-1 overflow-y-auto p-6 space-y-6 bg-white/30">
          <AnimatePresence>
            {messages.length === 0 && !loading && (
              <div className="h-full flex flex-col items-center justify-center text-center space-y-4 max-w-sm mx-auto">
                <div className="p-4 bg-gray-50 rounded-full">
                  <Sparkles size={32} className="text-pink-400" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-gray-700">Start a new chapter, Jan!</h2>
                  <p className="text-sm text-gray-400 mt-1">Our memory is clear and I'm ready to help you with anything.</p>
                </div>
              </div>
            )}
            {messages.map((msg, idx) => (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                key={idx}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`p-4 rounded-2xl max-w-[85%] shadow-sm ${
                  msg.role === 'user' 
                  ? 'bg-pink-600 text-white rounded-tr-none shadow-pink-200' 
                  : 'bg-white text-gray-800 rounded-tl-none border border-gray-100 shadow-pink-50/50'
                }`}>
                  <div className="prose prose-sm max-w-none text-inherit break-words leading-relaxed">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

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

        {/* Input Area */}
        <footer className="p-4 bg-white border-t border-gray-100">
          <form onSubmit={sendMessage} className="max-w-4xl mx-auto flex gap-3 bg-gray-50 p-2 rounded-2xl border border-gray-200 shadow-inner">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={`Send ${botName} a message...`}
              className="flex-1 bg-transparent p-2 pl-4 focus:outline-none text-gray-700 placeholder:text-gray-300"
            />
            <button
              type="submit"
              disabled={!input.trim() || loading}
              className="bg-pink-600 text-white p-3 rounded-xl hover:bg-pink-700 transition-all shadow-md disabled:opacity-40"
            >
              <Send size={18} />
            </button>
          </form>
          <p className="text-[9px] text-center text-gray-300 mt-2 uppercase tracking-tighter font-bold">Powered by Gemini • Context: Last 15 Msgs</p>
        </footer>
      </div>
    </div>
  );
}

export default App;