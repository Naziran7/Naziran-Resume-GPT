import React, { useEffect, useRef, useState } from "react";
import { api } from "../lib/api";
import { useAuth } from "../context/AuthContext";
import { 
  AlertCircle, ArrowLeft, Bot, BrainCircuit, CheckCircle2, 
  FileText, History, Loader2, Send, Trash2, UploadCloud, User 
} from "lucide-react";
import { Link } from "react-router-dom";

interface ChatSession {
  id: string;
  title: string;
  created_at: string;
}

interface ChatMessage {
  id?: string;
  role: "user" | "assistant";
  content: string;
  citations?: { files: string[] } | null;
  confidence_score?: number | null;
}

export const Chat: React.FC = () => {
  const { user } = useAuth();
  
  // Sidebar State
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [newSessionTitle, setNewSessionTitle] = useState("");
  const [sessionsLoading, setSessionsLoading] = useState(true);

  // Chat pane State
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [streamingResponse, setStreamingResponse] = useState("");
  
  // RAG Document Ingestion State
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [ingestedDocs, setIngestedDocs] = useState<{ id: string; file_name: string }[]>([]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load Sessions on mount
  useEffect(() => {
    fetchSessions();
    fetchIngestedDocs();
  }, []);

  const fetchIngestedDocs = async () => {
    try {
      const res = await api.get("/chatbot/documents");
      setIngestedDocs(res.data);
    } catch (err) {
      console.error("Failed to fetch ingested documents", err);
    }
  };

  const handleDeleteDoc = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await api.delete(`/chatbot/documents/${id}`);
      setIngestedDocs((prev) => prev.filter((d) => d.id !== id));
    } catch (err) {
      console.error("Failed to delete document", err);
    }
  };

  // Sync scroll on message length updates
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingResponse]);

  // Load Messages when active session shifts
  useEffect(() => {
    if (activeSessionId) {
      fetchMessages(activeSessionId);
    } else {
      setMessages([]);
    }
  }, [activeSessionId]);

  const fetchSessions = async () => {
    try {
      setSessionsLoading(true);
      const res = await api.get("/chatbot/sessions");
      setSessions(res.data);
      if (res.data.length > 0 && !activeSessionId) {
        setActiveSessionId(res.data[0].id);
      }
    } catch (err) {
      console.error("Failed to load chat sessions", err);
    } finally {
      setSessionsLoading(false);
    }
  };

  const fetchMessages = async (sid: string) => {
    try {
      setChatLoading(true);
      const res = await api.get(`/chatbot/sessions/${sid}/messages`);
      setMessages(res.data);
    } catch (err) {
      console.error("Failed to load session messages", err);
    } finally {
      setChatLoading(false);
    }
  };

  const handleCreateSession = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSessionTitle.trim()) return;
    try {
      const formData = new FormData();
      formData.append("title", newSessionTitle);
      const res = await api.post("/chatbot/sessions", formData);
      setSessions(prev => [res.data, ...prev]);
      setActiveSessionId(res.data.id);
      setNewSessionTitle("");
    } catch (err) {
      console.error("Failed to create chat session", err);
    }
  };

  const handleDeleteSession = async (sid: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this chat session?")) return;
    try {
      await api.delete(`/chatbot/sessions/${sid}`);
      setSessions(prev => prev.filter(s => s.id !== sid));
      if (activeSessionId === sid) {
        setActiveSessionId(null);
        setMessages([]);
      }
    } catch (err) {
      console.error("Failed to delete chat session", err);
    }
  };

  // Custom HTTP fetch request to stream response via SSE
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || !activeSessionId || chatLoading) return;

    const userText = inputText;
    setInputText("");
    
    // Add user message locally
    setMessages(prev => [...prev, { role: "user", content: userText }]);
    setChatLoading(true);
    setStreamingResponse("");

    try {
      const token = localStorage.getItem("access_token");
      const url = `${import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1"}/chatbot/sessions/${activeSessionId}/stream`;

      const formData = new FormData();
      formData.append("content", userText);

      // Perform fetch request manually to manage TextDecoder Stream
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`
        },
        body: formData
      });

      if (!response.ok) {
        throw new Error("Server-Sent Events connection failed.");
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) throw new Error("ReadableStream not supported on target browser.");

      let finished = false;
      let streamedBuffer = "";

      while (!finished) {
        const { value, done } = await reader.read();
        finished = done;
        if (value) {
          const chunkStr = decoder.decode(value, { stream: !done });
          // SSE encodes text with "data: " lines. Split and process
          const lines = chunkStr.split("\n");
          for (const line of lines) {
            if (line.trim().startsWith("data: ")) {
              try {
                const rawJson = line.trim().slice(6);
                const parsed = JSON.parse(rawJson);
                
                if (parsed.token) {
                  streamedBuffer += parsed.token;
                  setStreamingResponse(streamedBuffer);
                }
                
                if (parsed.done) {
                  // Message has saved to DB. Add response and reset
                  setMessages(prev => [
                    ...prev,
                    { 
                      role: "assistant", 
                      content: streamedBuffer,
                      citations: parsed.citations ? { files: parsed.citations } : null,
                      confidence_score: parsed.confidence_score
                    }
                  ]);
                  setStreamingResponse("");
                  setChatLoading(false);
                }
              } catch (parseErr) {
                // Ignore chunk parse issues (occurs on boundary fragment lines)
              }
            }
          }
        }
      }
    } catch (err) {
      console.error("Streaming message failed", err);
      setMessages(prev => [...prev, { role: "assistant", content: "Sorry, I encountered an error streaming that response." }]);
      setChatLoading(false);
    }
  };

  const handleIngestDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;

    try {
      setUploadLoading(true);
      setUploadError(null);
      setUploadSuccess(null);

      const formData = new FormData();
      formData.append("file", uploadFile);

      const res = await api.post("/chatbot/upload", formData);
      setUploadSuccess(res.data.message || "File uploaded successfully!");
      setUploadFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      fetchIngestedDocs();
    } catch (err: any) {
      const errMsg = err.response?.data?.error?.message || err.response?.data?.message || "Failed to upload document context.";
      setUploadError(errMsg);
    } finally {
      setUploadLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Header Bar */}
      <header className="flex items-center justify-between p-4 bg-slate-900/60 border-b border-slate-800 backdrop-blur-xl">
        <div className="flex items-center gap-3">
          <Link to="/" className="p-2 rounded-xl bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800 hover:bg-slate-900 transition">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div className="flex items-center gap-2">
            <BrainCircuit className="w-6 h-6 text-indigo-400" />
            <h1 className="text-lg font-bold">Enterprise RAG Assistant</h1>
          </div>
        </div>
        <div className="text-xs text-slate-400 font-medium">
          Logged in as: <span className="text-slate-200 font-semibold">{user?.email}</span>
        </div>
      </header>

      {/* Main Workspace */}
      <div className="flex-grow flex flex-col lg:flex-row overflow-hidden" style={{ height: "calc(100vh - 65px)" }}>
        {/* Sidebar */}
        <aside className="w-full lg:w-80 flex flex-col bg-slate-900/40 border-b lg:border-b-0 lg:border-r border-slate-900 p-4 shrink-0 overflow-y-auto">
          {/* Document upload Box */}
          <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-900/80 mb-5">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <UploadCloud className="w-4 h-4 text-indigo-400" /> Ingest Knowledge
            </h3>
            
            <form onSubmit={handleIngestDocument} className="space-y-3">
              <div 
                onClick={() => fileInputRef.current?.click()}
                className="border border-dashed border-slate-800 rounded-xl p-4 text-center cursor-pointer hover:border-slate-700 hover:bg-slate-900/20 transition duration-150"
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  className="hidden"
                  accept=".pdf,.docx,.doc,.txt"
                />
                {uploadFile ? (
                  <div className="flex items-center justify-center gap-1.5 text-xs text-slate-300">
                    <FileText className="w-4 h-4 text-indigo-500 shrink-0" />
                    <span className="truncate max-w-[160px] font-medium">{uploadFile.name}</span>
                  </div>
                ) : (
                  <p className="text-xs text-slate-500">Click to upload doc context (PDF/DOCX/TXT)</p>
                )}
              </div>

              {uploadSuccess && (
                <div className="flex items-start gap-1.5 p-2.5 rounded-lg bg-emerald-950/20 border border-emerald-500/20 text-emerald-400 text-xs">
                  <CheckCircle2 className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                  <span>{uploadSuccess}</span>
                </div>
              )}

              {uploadError && (
                <div className="flex items-start gap-1.5 p-2.5 rounded-lg bg-red-950/20 border border-red-500/20 text-red-400 text-xs">
                  <AlertCircle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                  <span>{uploadError}</span>
                </div>
              )}

              {uploadFile && (
                <button
                  type="submit"
                  disabled={uploadLoading}
                  className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs disabled:opacity-50 transition duration-150"
                >
                  {uploadLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : "Calculate Embeddings"}
                </button>
              )}
            </form>

            {/* Active Ingested Documents List */}
            {ingestedDocs.length > 0 && (
              <div className="mt-4 pt-3 border-t border-slate-900 space-y-2">
                <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Active Context Documents ({ingestedDocs.length})</p>
                <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
                  {ingestedDocs.map((doc) => (
                    <div key={doc.id} className="flex items-center justify-between p-2 rounded-lg bg-slate-900/60 border border-slate-800 text-xs">
                      <div className="flex items-center gap-2 min-w-0">
                        <FileText className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                        <span className="truncate text-slate-300 text-[11px]" title={doc.file_name}>{doc.file_name}</span>
                      </div>
                      <button
                        onClick={(e) => handleDeleteDoc(doc.id, e)}
                        className="p-1 text-slate-500 hover:text-red-400 transition shrink-0"
                        title="Remove document from context"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* New Session Trigger */}
          <form onSubmit={handleCreateSession} className="flex gap-2 mb-4">
            <input
              type="text"
              placeholder="New session title..."
              value={newSessionTitle}
              onChange={(e) => setNewSessionTitle(e.target.value)}
              className="flex-grow py-2 px-3 rounded-xl bg-slate-950 border border-slate-900 focus:outline-none focus:border-slate-800 text-sm"
            />
            <button
              type="submit"
              className="py-2 px-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shrink-0 transition"
            >
              Create
            </button>
          </form>

          {/* Session List */}
          <div className="flex-grow space-y-2 overflow-y-auto pr-1">
            <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <History className="w-3.5 h-3.5" /> Sessions History
            </h4>

            {sessionsLoading ? (
              <div className="flex justify-center py-6 text-slate-500">
                <Loader2 className="w-5 h-5 animate-spin" />
              </div>
            ) : sessions.length === 0 ? (
              <p className="text-xs text-slate-600 italic p-3 text-center">No active chat sessions.</p>
            ) : (
              sessions.map((s) => (
                <div
                  key={s.id}
                  onClick={() => setActiveSessionId(s.id)}
                  className={`group w-full flex items-center justify-between p-3 rounded-xl border text-sm cursor-pointer transition ${
                    activeSessionId === s.id
                      ? "bg-indigo-600/10 border-indigo-500/30 text-slate-200"
                      : "bg-slate-950/30 border-transparent text-slate-400 hover:bg-slate-900/20 hover:text-slate-300"
                  }`}
                >
                  <span className="truncate max-w-[160px] font-medium">{s.title}</span>
                  <button
                    onClick={(e) => handleDeleteSession(s.id, e)}
                    className="p-1 rounded bg-transparent opacity-0 group-hover:opacity-100 hover:bg-red-950/30 hover:text-red-400 text-slate-500 transition"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))
            )}
          </div>
        </aside>

        {/* Chat Interface */}
        <main className="flex-grow flex flex-col bg-slate-950 relative overflow-hidden">
          {activeSessionId ? (
            <>
              {/* Message Streams */}
              <div className="flex-grow overflow-y-auto p-6 space-y-5">
                {messages.map((m, idx) => (
                  <div key={idx} className={`flex gap-4 ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                    
                    {/* Bot avatar */}
                    {m.role === "assistant" && (
                      <div className="w-8 h-8 rounded-full bg-indigo-950/50 border border-indigo-500/20 flex items-center justify-center shrink-0">
                        <Bot className="w-4 h-4 text-indigo-400" />
                      </div>
                    )}

                    {/* Content wrapper */}
                    <div className="max-w-[75%] space-y-2">
                      <div className={`p-4 rounded-2xl text-sm leading-relaxed border ${
                        m.role === "user"
                          ? "bg-indigo-600/10 border-indigo-500/20 text-indigo-100 rounded-tr-none"
                          : "bg-slate-900/60 border-slate-900 text-slate-200 rounded-tl-none backdrop-blur-md"
                      }`}>
                        <p className="whitespace-pre-wrap">{m.content}</p>
                      </div>

                      {/* Assistant RAG Metadata: Citations & Confidence metrics */}
                      {m.role === "assistant" && (m.citations?.files || m.confidence_score !== undefined) && (
                        <div className="flex flex-wrap items-center gap-3 px-2 text-[10px] text-slate-500 font-semibold uppercase tracking-wider">
                          {m.confidence_score !== null && m.confidence_score !== undefined && (
                            <div className="flex items-center gap-1">
                              <BrainCircuit className="w-3.5 h-3.5 text-indigo-500" />
                              <span>Match score: {(m.confidence_score * 100).toFixed(0)}%</span>
                            </div>
                          )}
                          {m.citations?.files && m.citations.files.length > 0 && (
                            <div className="flex items-center gap-1 bg-slate-900/50 py-0.5 px-2 rounded-md border border-slate-800 text-indigo-400">
                              <FileText className="w-3 h-3" />
                              <span>Sources: {m.citations.files.join(", ")}</span>
                            </div>
                          )}
                        </div>
                      )}
                    </div>

                    {/* User avatar */}
                    {m.role === "user" && (
                      <div className="w-8 h-8 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center shrink-0">
                        <User className="w-4 h-4 text-slate-400" />
                      </div>
                    )}

                  </div>
                ))}

                {/* Render live text tokens during streaming */}
                {streamingResponse && (
                  <div className="flex gap-4 justify-start">
                    <div className="w-8 h-8 rounded-full bg-indigo-950/50 border border-indigo-500/20 flex items-center justify-center shrink-0">
                      <Bot className="w-4 h-4 text-indigo-400" />
                    </div>
                    <div className="max-w-[75%]">
                      <div className="p-4 rounded-2xl text-sm leading-relaxed border bg-slate-900/60 border-slate-900 text-slate-200 rounded-tl-none backdrop-blur-md">
                        <p className="whitespace-pre-wrap">{streamingResponse}</p>
                      </div>
                    </div>
                  </div>
                )}

                {chatLoading && !streamingResponse && (
                  <div className="flex gap-4 justify-start">
                    <div className="w-8 h-8 rounded-full bg-indigo-950/50 border border-indigo-500/20 flex items-center justify-center shrink-0">
                      <Bot className="w-4 h-4 text-indigo-400 animate-pulse" />
                    </div>
                    <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-900 text-slate-400 text-xs italic flex items-center gap-2">
                      <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-400" />
                      <span>RAG vector searching in progress...</span>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Message Form Box */}
              <div className="p-4 bg-slate-900/20 border-t border-slate-900 backdrop-blur-md">
                <form onSubmit={handleSendMessage} className="flex gap-3 max-w-5xl mx-auto">
                  <input
                    type="text"
                    placeholder="Ask standard handbook guidelines or check resumes gaps criteria..."
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    disabled={chatLoading}
                    className="flex-grow py-3 px-4 rounded-2xl bg-slate-950 border border-slate-900 focus:outline-none focus:border-slate-800 text-sm disabled:opacity-50"
                  />
                  <button
                    type="submit"
                    disabled={chatLoading || !inputText.trim()}
                    className="p-3.5 rounded-2xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white shrink-0 shadow-lg shadow-indigo-950/20 hover:shadow-indigo-950/40 transition duration-150"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </form>
              </div>
            </>
          ) : (
            <div className="flex-grow flex flex-col items-center justify-center text-slate-500">
              <Bot className="w-12 h-12 text-slate-700 mb-3" />
              <p className="text-sm font-medium">Select or create a chat session to get started.</p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};
