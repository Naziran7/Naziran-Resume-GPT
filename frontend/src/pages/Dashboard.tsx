import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { api, API_BASE_URL } from "../lib/api";
import { 
  UploadCloud, FileText, Download, User, LogOut, 
  CheckCircle2, ChevronRight, AlertCircle, Sparkles, BrainCircuit, Trash2
} from "lucide-react";
import { Link } from "react-router-dom";
import { RecommendationsView } from "../components/RecommendationsView";

interface ResumeAnalysis {
  id: string;
  ats_score: number;
  feedback: {
    score_breakdown: Record<string, number>;
    suggestions: string[];
    word_count: number;
  };
}

interface Resume {
  id: string;
  file_name: string;
  file_url: string;
  file_size: number;
  created_at: string;
  analysis?: ResumeAnalysis;
}

export const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [targetJd, setTargetJd] = useState("");
  const [selectedResume, setSelectedResume] = useState<Resume | null>(null);
  const [rescoring, setRescoring] = useState(false);

  const handleCheckJdMatch = async () => {
    if (!targetJd.trim()) {
      setUploadError("Please paste a target job description to check compatibility.");
      return;
    }
    setUploadError(null);

    if (selectedResume) {
      setRescoring(true);
      try {
        const response = await api.post(`/resumes/${selectedResume.id}/rescore`, {
          target_job_description: targetJd.trim()
        });
        setSelectedResume(response.data);
      } catch (err: any) {
        setUploadError(err.message || "Failed to rescore resume against target job description.");
      } finally {
        setRescoring(false);
      }
    } else {
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      if (fileInput) {
        fileInput.click();
      }
    }
  };
  const [activeTab, setActiveTab] = useState<"insights" | "recommendations">("insights");

  useEffect(() => {
    setActiveTab("insights");
  }, [selectedResume]);

  // Drag and drop states
  const [isDragActive, setIsDragActive] = useState(false);

  const fetchResumes = async () => {
    try {
      await api.get("/resumes/my-resumes");
      // Resumes fetched but not auto-selected so dashboard opens clean
    } catch (err) {
      console.error("Error fetching resumes:", err);
    }
  };

  const handleDeleteResume = async (id: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    try {
      await api.delete(`/resumes/${id}`);
      if (selectedResume?.id === id) {
        setSelectedResume(null);
      }
      fetchResumes();
    } catch (err) {
      console.error("Error deleting resume:", err);
    }
  };

  useEffect(() => {
    fetchResumes();
  }, []);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragActive(true);
    } else if (e.type === "dragleave") {
      setIsDragActive(false);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await uploadFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      await uploadFile(e.target.files[0]);
    }
  };

  const uploadFile = async (file: File) => {
    const ext = file.name.split(".").pop()?.toLowerCase();
    if (ext !== "pdf" && ext !== "docx" && ext !== "doc") {
      setUploadError("Invalid file type. Please upload a PDF or DOCX file.");
      return;
    }

    setUploadError(null);
    setUploading(true);

    const formData = new FormData();
    formData.append("file", file);
    if (targetJd.trim()) {
      formData.append("target_job_description", targetJd.trim());
    }

    try {
      const response = await api.post("/resumes/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      setSelectedResume(response.data);
      setTargetJd(""); // Clear the job description text after upload
    } catch (err: any) {
      setUploadError(err.message || "Failed to process and analyze resume.");
    } finally {
      setUploading(false);
    }
  };

  const handleDownloadReport = async (id: string, fileName?: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    try {
      const res = await api.get(`/resumes/${id}/report`, {
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([res.data], { type: "application/pdf" }));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `NaziranGPT_Report_${fileName || id}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      console.error("Error downloading report via blob, opening direct token link:", err);
      const token = localStorage.getItem("access_token");
      window.open(`${API_BASE_URL}/resumes/${id}/report?token=${token}`, "_blank");
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 75) return "text-emerald-400 border-emerald-500/35 bg-emerald-500/10";
    if (score >= 50) return "text-amber-400 border-amber-500/35 bg-amber-500/10";
    return "text-red-400 border-red-500/35 bg-red-500/10";
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      {/* Top Premium Navbar */}
      <header className="border-b border-border bg-card/40 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center font-bold text-white text-lg shadow-lg shadow-indigo-500/20">
              N
            </div>
            <span className="font-bold text-xl tracking-tight bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
              NaziranGPT
            </span>
          </div>

          <div className="flex items-center gap-4">
            <Link to="/chat" className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border hover:bg-secondary/40 text-sm transition-all text-slate-300">
              <BrainCircuit className="w-4 h-4 text-primary" />
              <span>AI Chatbot</span>
            </Link>
            <Link to="/profile" className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border hover:bg-secondary/40 text-sm transition-all text-slate-300">
              <User className="w-4 h-4 text-primary" />
              <span>{user?.full_name || "Profile"}</span>
            </Link>
            <button 
              onClick={logout} 
              className="p-2 rounded-lg border border-border hover:bg-destructive/10 text-slate-400 hover:text-destructive-foreground transition-all"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-8 grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Side: Upload & Resume Listing (7 Cols) */}
        <section className="lg:col-span-7 space-y-8">
          
          {/* Drag & Drop Upload Panel */}
          <div className="glass-panel p-6 rounded-2xl border border-white/10 relative">
            <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-primary" />
              Upload & Scan Resume
            </h2>

            {/* Optional JD match input */}
            <div className="mb-4">
              <label className="text-xs text-slate-400 font-semibold uppercase tracking-wider block mb-1">
                Target Job Description (Optional keywords match)
              </label>
              <textarea
                value={targetJd}
                onChange={(e) => setTargetJd(e.target.value)}
                placeholder="Paste the target job description here to calculate a specific skills keyword compatibility score..."
                className="w-full h-20 p-3 bg-secondary/30 border border-border rounded-lg text-xs text-white placeholder-muted-foreground focus:outline-none focus:border-primary transition-all resize-none"
              />
              <div className="mt-2 flex justify-end">
                <button
                  type="button"
                  onClick={handleCheckJdMatch}
                  disabled={rescoring || uploading}
                  className="px-4 py-2 bg-primary hover:bg-primary/90 text-white font-semibold rounded-lg text-xs transition-all flex items-center gap-2 shadow-lg shadow-indigo-500/20 disabled:opacity-50"
                >
                  {rescoring ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                      <span>Checking Match...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Check Now</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            <div 
              onDragEnter={handleDrag}
              onDragOver={handleDrag}
              onDragLeave={handleDrag}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center transition-all relative ${
                isDragActive 
                  ? "border-primary bg-primary/5" 
                  : "border-white/10 bg-secondary/10 hover:bg-secondary/20 hover:border-white/20"
              }`}
            >
              {uploading ? (
                <div className="flex flex-col items-center py-4">
                  <div className="w-10 h-10 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
                  <p className="text-sm font-semibold text-white mt-4">AI Parsing & ATS Scoring in Progress...</p>
                  <p className="text-xs text-muted-foreground mt-1">Reading sections, mapping skills, and compiling report...</p>
                </div>
              ) : (
                <>
                  <UploadCloud className="w-12 h-12 text-primary/60 mb-3" />
                  <p className="text-sm font-medium text-slate-200">
                    Drag and drop your resume here, or{" "}
                    <label className="text-primary hover:underline cursor-pointer">
                      browse
                      <input 
                        type="file" 
                        onChange={handleFileChange} 
                        className="hidden" 
                        accept=".pdf,.docx,.doc" 
                      />
                    </label>
                  </p>
                  <p className="text-xs text-muted-foreground mt-2">
                    Supports PDF, DOCX (Max 10MB)
                  </p>
                </>
              )}
            </div>

            {uploadError && (
              <div className="mt-4 p-4 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive-foreground text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-destructive shrink-0" />
                <span>{uploadError}</span>
              </div>
            )}
          </div>
        </section>

        {/* Right Side: ATS Score breakdown & Recommendations (5 Cols) */}
        <section className="lg:col-span-5">
          {selectedResume ? (
            <div className="glass-panel p-6 rounded-2xl border border-white/10 sticky top-24 space-y-6">
              <div className="border-b border-border pb-4 flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold text-white">Score Insights</h2>
                  <div className="flex items-center gap-2 mt-0.5">
                    <p className="text-xs text-muted-foreground truncate max-w-[140px]" title={selectedResume.file_name}>
                      {selectedResume.file_name}
                    </p>
                    <button
                      onClick={(e) => handleDeleteResume(selectedResume.id, e)}
                      className="p-1 rounded text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                      title="Delete saved resume"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
                
                <div className="flex bg-slate-950 p-1 rounded-lg border border-border text-[11px] font-bold">
                  <button
                    onClick={() => setActiveTab("insights")}
                    className={`px-3 py-1.5 rounded-md transition ${
                      activeTab === "insights" ? "bg-primary text-white" : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    ATS
                  </button>
                  <button
                    onClick={() => setActiveTab("recommendations")}
                    className={`px-3 py-1.5 rounded-md transition ${
                      activeTab === "recommendations" ? "bg-primary text-white" : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    Roadmap
                  </button>
                </div>
              </div>

              {activeTab === "insights" ? (
                <>
                  {/* Large Score Indicator */}
                  <div className="flex items-center justify-between p-4 rounded-xl bg-secondary/20 border border-white/5">
                    <div>
                      <h3 className="text-sm font-semibold text-slate-300">ATS Score</h3>
                      <p className="text-xs text-muted-foreground mt-1">Computed by scoring engine</p>
                    </div>
                    <div className="relative flex items-center justify-center">
                      <div className={`w-16 h-16 rounded-full border-4 flex items-center justify-center text-xl font-bold ${
                        selectedResume.analysis ? getScoreColor(selectedResume.analysis.ats_score).split(" ").slice(0,2).join(" ") : "border-border text-slate-400"
                      }`}>
                        {selectedResume.analysis?.ats_score || 0}
                      </div>
                    </div>
                  </div>

                  {/* Suggestions Section */}
                  <div className="space-y-3">
                    <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4 text-primary" />
                      Actionable Recommendations
                    </h3>
                    
                    {selectedResume.analysis?.feedback?.suggestions && selectedResume.analysis.feedback.suggestions.length > 0 ? (
                      <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
                        {selectedResume.analysis.feedback.suggestions.map((suggestion, i) => (
                          <div key={i} className="p-3 rounded-lg bg-secondary/10 border border-border text-xs text-slate-300 flex items-start gap-2.5">
                            <ChevronRight className="w-3.5 h-3.5 text-primary shrink-0 mt-0.5" />
                            <span>{suggestion}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-muted-foreground italic">No suggestions provided for this resume.</p>
                    )}
                  </div>

                  {/* Download Full report button */}
                  <button
                    onClick={(e) => handleDownloadReport(selectedResume.id, selectedResume.file_name, e)}
                    className="w-full py-2.5 px-4 bg-secondary border border-border hover:border-white/20 text-white font-medium rounded-lg text-sm transition-all flex items-center justify-center gap-2"
                  >
                    <Download className="w-4 h-4 text-primary" />
                    Download PDF Report
                  </button>
                </>
              ) : (
                <div className="max-h-[500px] overflow-y-auto pr-1">
                  <RecommendationsView resumeId={selectedResume.id} />
                </div>
              )}

            </div>
          ) : (
            <div className="glass-panel p-8 rounded-2xl border border-white/10 text-center text-muted-foreground flex flex-col items-center justify-center h-64 sticky top-24">
              <FileText className="w-8 h-8 mb-2 opacity-50" />
              <p className="text-sm font-semibold">No analysis loaded</p>
              <p className="text-xs mt-1">Select a scan from history or upload a new file to display insights.</p>
            </div>
          )}
        </section>

      </main>
    </div>
  );
};
