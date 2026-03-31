import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Send, Heart, Sparkles, User } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { motion, AnimatePresence } from 'framer-motion';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [botName, setBotName] = useState('Assistant'); // Dynamic Name State
  const scrollRef = useRef(null);

  // 1. Fetch Config from FastAPI on Page Load
  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const response = await axios.get("http://127.0.0.1:8000/config");
        // We use the key 'bot_name' we defined in the FastAPI /config route
        setBotName(response.data.bot_name);
      } catch (err) {
        console.error("Could not fetch backend config:", err);
      }
    };
    fetchConfig();
  }, []);

  // 2. Auto-scroll to bottom
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // 3. Send Message Logic
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
        `http://127.0.0.1:8000/chat?user_message=${encodeURIComponent(currentInput)}`
      );
      
      // Grab the reply from the dynamic key (botName) or the first value
      const botReply = response.data[botName] || Object.values(response.data)[0];
      
      setMessages(prev => [...prev, { role: 'bot', content: botReply }]);
    } catch (error) {
      console.error("Chat Error:", error);
      setMessages(prev => [...prev, { role: 'bot', content: "Connection to server lost. 💔" }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-[#F7F9FB] font-sans text-gray-900">
      {/* Dynamic Header */}
      <header className="bg-white/80 backdrop-blur-md sticky top-0 z-10 border-b border-gray-100 p-4 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-3">
          <div className="bg-gradient-to-tr from-pink-500 to-rose-400 p-2 rounded-xl shadow-sm">
            <Sparkles className="text-white" size={18} />
          </div>
          <div>
            <h1 className="text-lg font-bold text-gray-800 capitalize">{botName}</h1>
            <p className="text-[10px] text-green-500 font-semibold uppercase tracking-wider">Online & Active</p>
          </div>
        </div>
      </header>

      {/* Chat Area */}
      <main className="flex-1 overflow-y-auto p-4 space-y-6">
        <AnimatePresence>
          {messages.map((msg, idx) => (
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              key={idx} 
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`flex gap-3 max-w-[85%] ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                <div className={`p-4 rounded-2xl shadow-sm ${
                  msg.role === 'user' 
                  ? 'bg-pink-600 text-white rounded-tr-none' 
                  : 'bg-white text-gray-800 rounded-tl-none border border-gray-100'
                }`}>
                  {/* ✅ NEW FIXED WAY */}
<div className="prose prose-sm max-w-none break-words overflow-hidden text-inherit">
  <ReactMarkdown>
    {msg.content}
  </ReactMarkdown>
</div>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        
        {loading && (
          <div className="flex justify-start">
             <div className="bg-white border border-gray-100 p-3 rounded-2xl rounded-tl-none flex gap-1">
               <span className="w-1.5 h-1.5 bg-pink-400 rounded-full animate-bounce"></span>
               <span className="w-1.5 h-1.5 bg-pink-400 rounded-full animate-bounce [animation-delay:0.2s]"></span>
               <span className="w-1.5 h-1.5 bg-pink-400 rounded-full animate-bounce [animation-delay:0.4s]"></span>
             </div>
          </div>
        )}
        <div ref={scrollRef} />
      </main>

      {/* Dynamic Input Area */}
      <footer className="p-4 bg-white border-t border-gray-100">
        <form onSubmit={sendMessage} className="max-w-4xl mx-auto flex gap-3 bg-gray-50 p-2 rounded-2xl border border-gray-200 shadow-inner">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={`Talk to ${botName}...`}
            className="flex-1 bg-transparent p-2 pl-4 focus:outline-none text-gray-700"
          />
          <button 
            type="submit" 
            disabled={!input.trim() || loading}
            className="bg-pink-600 text-white p-3 rounded-xl hover:bg-pink-700 transition-all disabled:opacity-30 shadow-md"
          >
            <Send size={18} />
          </button>
        </form>
      </footer>
    </div>
  );
}

export default App;