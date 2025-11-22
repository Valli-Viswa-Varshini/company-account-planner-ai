import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, FileText, Loader2, Edit3, Check, Sparkles, MessageCircle, Mic, Link } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { motion, AnimatePresence } from 'framer-motion';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs) {
  return twMerge(clsx(inputs));
}

function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', text: 'Hi! I\'m your AI Research Assistant. I can help you research companies and generate strategic account plans. Which company would you like to learn about?' }
  ]);
  const [input, setInput] = useState('');
  const [plan, setPlan] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [editingSection, setEditingSection] = useState(null);
  const [editContent, setEditContent] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [sources, setSources] = useState([]);
  const [showSources, setShowSources] = useState(false);

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setIsLoading(true);

    // Add user message
    setMessages(prev => [...prev, { role: 'user', text: userMessage }]);

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          conversation_history: messages.map(m => ({ role: m.role, content: m.text }))
        }),
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const event = JSON.parse(line);

            // Handle different event types
            if (event.type === 'message') {
              const msg = { role: event.role, text: event.content };
              setMessages(prev => [...prev, msg]);
              // Speak agent responses if voice is enabled
              if (event.role === 'assistant') {
                speakText(event.content);
              }
            }
            else if (event.type === 'agent_event') {
              // LangGraph events
              const data = event.data;
              for (const nodeName in data) {
                const stateUpdate = data[nodeName];

                if (stateUpdate.messages && Array.isArray(stateUpdate.messages)) {
                  stateUpdate.messages.forEach(msg => {
                    setMessages(prev => [...prev, { role: 'assistant', text: msg }]);
                    speakText(msg);
                  });
                }

                if (stateUpdate.sources && Array.isArray(stateUpdate.sources)) {
                  setSources(prev => [...prev, ...stateUpdate.sources]);
                }

                if (stateUpdate.plan_sections) {
                  setPlan(stateUpdate.plan_sections);
                  const successMsg = '✅ I\'ve generated a comprehensive Strategic Account Plan. You can view it on the right, and feel free to ask me to update any section!';
                  setMessages(prev => [...prev, {
                    role: 'assistant',
                    text: successMsg
                  }]);
                  speakText(successMsg);
                }
              }
            }
            else if (event.type === 'error') {
              setMessages(prev => [...prev, { role: 'assistant', text: `❌ Error: ${event.message}` }]);
            }
          } catch (e) {
            console.error("Error parsing JSON:", e, "Line:", line);
          }
        }
      }
    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', text: `❌ Connection Error: ${error.message}` }]);
    } finally {
      setIsLoading(false);
    }
  };

  // Voice Input (Speech Recognition)
  const startListening = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      alert('Speech recognition not supported in this browser. Try Chrome!');
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.continuous = false;

    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setInput(transcript);
    };

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      setIsListening(false);
    };

    recognition.start();
  };

  // Voice Output (Text-to-Speech)
  const speakText = (text) => {
    if ('speechSynthesis' in window) {
      // Cancel any ongoing speech
      window.speechSynthesis.cancel();

      // Remove markdown formatting for better speech
      const cleanText = text.replace(/[*_#`]/g, '').replace(/\[.*?\]\(.*?\)/g, '');

      const utterance = new SpeechSynthesisUtterance(cleanText);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      utterance.volume = 0.8;
      window.speechSynthesis.speak(utterance);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleEdit = (key, content) => {
    setEditingSection(key);
    setEditContent(content);
  };

  const saveEdit = (key) => {
    setPlan(prev => ({ ...prev, [key]: editContent }));
    setEditingSection(null);
    setMessages(prev => [...prev, {
      role: 'assistant',
      text: `✅ I've updated the **${key.replace(/_/g, ' ')}** section for you!`
    }]);
  };

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans selection:bg-indigo-500/30">

      {/* Left Panel: Chat */}
      <div className="w-1/3 flex flex-col border-r border-slate-800 bg-slate-900/50 backdrop-blur-xl">

        {/* Header */}
        <div className="p-6 border-b border-slate-800 flex items-center gap-3">
          <div className="p-2 bg-indigo-600 rounded-lg shadow-lg shadow-indigo-500/20">
            <MessageCircle className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent">
              Research Assistant
            </h1>
            <p className="text-xs text-slate-400">Conversational AI Agent</p>
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
          <AnimatePresence>
            {messages.map((msg, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={cn(
                  "flex gap-3 max-w-[90%]",
                  msg.role === 'user' ? "ml-auto flex-row-reverse" : ""
                )}
              >
                <div className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center shrink-0",
                  msg.role === 'user' ? "bg-slate-700" : "bg-indigo-600/20 text-indigo-400"
                )}>
                  {msg.role === 'user' ? <User size={14} /> : <Sparkles size={14} />}
                </div>
                <div className={cn(
                  "p-3 rounded-2xl text-sm leading-relaxed shadow-sm",
                  msg.role === 'user'
                    ? "bg-slate-800 text-slate-200 rounded-tr-none"
                    : "bg-slate-800/50 border border-slate-700/50 text-slate-300 rounded-tl-none"
                )}>
                  <ReactMarkdown>{msg.text}</ReactMarkdown>
                </div>
              </motion.div>
            ))}
            {isLoading && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-indigo-600/20 flex items-center justify-center shrink-0">
                  <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
                </div>
                <div className="text-xs text-slate-500 flex items-center">
                  Thinking...
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/80">
          <div className="relative">
            <textarea
              placeholder="Type or speak your message... (e.g., 'Tell me about Tesla')"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-3 pr-24 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all resize-none h-20"
            />
            <div className="absolute bottom-3 right-3 flex gap-2">
              <button
                onClick={startListening}
                disabled={isLoading || isListening}
                className={cn(
                  "p-2 rounded-md transition-colors shadow-lg",
                  isListening
                    ? "bg-red-600 animate-pulse"
                    : "bg-slate-700 hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed"
                )}
                title="Voice Input"
              >
                <Mic className="w-4 h-4 text-white" />
              </button>
              <button
                onClick={sendMessage}
                disabled={isLoading || !input.trim()}
                className="p-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-md disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-lg shadow-indigo-500/20"
              >
                {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* Sources Button */}
          {sources.length > 0 && (
            <button
              onClick={() => setShowSources(!showSources)}
              className="mt-2 text-xs text-slate-400 hover:text-indigo-400 flex items-center gap-1 transition-colors"
            >
              <Link size={12} />
              {sources.length} sources used
            </button>
          )}

          {/* Sources Panel */}
          {showSources && sources.length > 0 && (
            <div className="mt-2 p-3 bg-slate-950 border border-slate-800 rounded-lg max-h-40 overflow-y-auto">
              <p className="text-xs font-semibold text-slate-300 mb-2">Research Sources:</p>
              {sources.map((url, idx) => (
                <a
                  key={idx}
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block text-xs text-indigo-400 hover:text-indigo-300 truncate mb-1"
                >
                  {url}
                </a>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Right Panel: Account Plan */}
      <div className="flex-1 bg-slate-950 overflow-y-auto p-8 scrollbar-thin scrollbar-thumb-slate-800">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-2xl font-bold text-white flex items-center gap-3">
              <FileText className="text-indigo-400" />
              Strategic Account Plan
            </h2>
            {plan && (
              <span className="px-3 py-1 rounded-full bg-green-500/10 text-green-400 text-xs border border-green-500/20">
                Generated Successfully
              </span>
            )}
          </div>

          {!plan ? (
            <div className="h-[60vh] flex flex-col items-center justify-center text-slate-600 border-2 border-dashed border-slate-800 rounded-2xl bg-slate-900/20">
              <Bot className="w-16 h-16 mb-4 opacity-20" />
              <p>Ask me to research a company to generate a plan</p>
            </div>
          ) : (
            <div className="grid gap-6">
              {Object.entries(plan).map(([key, content], idx) => (
                <motion.div
                  key={key}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.1 }}
                  className="group bg-slate-900/50 border border-slate-800 rounded-xl p-6 hover:border-indigo-500/30 transition-colors"
                >
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-indigo-200 capitalize">
                      {key.replace(/_/g, ' ')}
                    </h3>
                    <button
                      onClick={() => editingSection === key ? saveEdit(key) : handleEdit(key, content)}
                      className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                    >
                      {editingSection === key ? <Check size={16} /> : <Edit3 size={16} />}
                    </button>
                  </div>

                  {editingSection === key ? (
                    <textarea
                      value={editContent}
                      onChange={(e) => setEditContent(e.target.value)}
                      className="w-full h-40 bg-slate-950 border border-slate-700 rounded-lg p-4 text-sm text-slate-300 focus:ring-2 focus:ring-indigo-500/50 focus:outline-none"
                    />
                  ) : (
                    <div className="prose prose-invert prose-sm max-w-none text-slate-300">
                      <ReactMarkdown>{content}</ReactMarkdown>
                    </div>
                  )}
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
