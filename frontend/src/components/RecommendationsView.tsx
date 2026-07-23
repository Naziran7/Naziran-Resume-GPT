import React, { useEffect, useState } from "react";
import { api } from "../lib/api";
import { AlertCircle, Award, BookOpen, CheckCircle, ChevronRight, Compass, Cpu, Loader2 } from "lucide-react";

interface RecommendationsViewProps {
  resumeId: string;
}

interface GapAnalysisDetail {
  match_percentage: number;
  matching_skills: string[];
  missing_skills: string[];
}

interface RecommendationResponse {
  gap_analysis: Record<string, GapAnalysisDetail>;
  roadmap: {
    target_role: string;
    skill_gap_summary: string;
    steps: string[];
  };
  certifications: string[];
  courses: string[];
}

export const RecommendationsView: React.FC<RecommendationsViewProps> = ({ resumeId }) => {
  const [data, setData] = useState<RecommendationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedRole, setSelectedRole] = useState<string>("");

  useEffect(() => {
    const fetchRecommendations = async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await api.get(`/resumes/${resumeId}/recommendations`);
        setData(res.data);
        
        // Auto-select best matching role based on percentage
        if (res.data?.gap_analysis) {
          const roles = Object.entries(res.data.gap_analysis) as [string, GapAnalysisDetail][];
          const best = roles.reduce((max, current) => 
            current[1].match_percentage > max[1].match_percentage ? current : max
          , roles[0]);
          setSelectedRole(best[0]);
        }
      } catch (err: any) {
        console.error("Failed to load career path recommendations", err);
        setError(err.response?.data?.message || "Failed to load career path recommendations.");
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, [resumeId]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-slate-400">
        <Loader2 className="w-10 h-10 animate-spin text-indigo-500 mb-3" />
        <p className="text-sm font-medium">Analyzing skill gaps and compiling custom roadmap...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex items-center gap-3 p-4 rounded-xl bg-red-950/30 border border-red-500/20 text-red-400 my-4">
        <AlertCircle className="w-5 h-5 flex-shrink-0" />
        <p className="text-sm font-medium">{error || "No recommendation details available."}</p>
      </div>
    );
  }

  const selectedAnalysis = data.gap_analysis[selectedRole];

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Skill Gaps Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Role Selector list */}
        <div className="lg:col-span-1 p-5 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl">
          <h3 className="text-base font-semibold text-slate-200 mb-4 flex items-center gap-2">
            <Compass className="w-5 h-5 text-indigo-400" /> Target Paths
          </h3>
          <div className="space-y-2">
            {Object.entries(data.gap_analysis).map(([role, analysis]) => (
              <button
                key={role}
                onClick={() => setSelectedRole(role)}
                className={`w-full flex items-center justify-between p-3.5 rounded-xl border transition-all duration-200 text-left ${
                  selectedRole === role
                    ? "bg-indigo-600/20 border-indigo-500/40 text-slate-100 shadow-lg shadow-indigo-950/20"
                    : "bg-slate-950/40 border-slate-900 text-slate-400 hover:border-slate-800 hover:text-slate-300"
                }`}
              >
                <span className="text-sm font-medium">{role}</span>
                <span className="text-xs px-2 py-1 rounded-md bg-slate-950 font-semibold text-indigo-400 border border-slate-800">
                  {analysis.match_percentage}% Match
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Selected Role Skill Grid */}
        <div className="lg:col-span-2 p-6 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-5">
              <h3 className="text-lg font-bold text-slate-200">{selectedRole} Gap Analysis</h3>
              <div className="flex items-center gap-2">
                <span className="text-2xl font-black text-indigo-400">{selectedAnalysis.match_percentage}%</span>
                <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">match score</span>
              </div>
            </div>
            
            {/* Visual Bar */}
            <div className="w-full bg-slate-950 h-3 rounded-full overflow-hidden border border-slate-800 mb-6">
              <div 
                className="h-full bg-gradient-to-r from-violet-600 to-indigo-500 rounded-full transition-all duration-500" 
                style={{ width: `${selectedAnalysis.match_percentage}%` }}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {/* Matching Skills */}
              <div className="p-4 rounded-xl bg-emerald-950/10 border border-emerald-500/10">
                <h4 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                  <CheckCircle className="w-4 h-4" /> Matching ({selectedAnalysis.matching_skills.length})
                </h4>
                {selectedAnalysis.matching_skills.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {selectedAnalysis.matching_skills.map((skill) => (
                      <span key={skill} className="text-xs px-2.5 py-1 rounded-md bg-emerald-950/20 text-emerald-400 border border-emerald-500/20 font-medium">
                        {skill}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500">No matching skills detected in this category.</p>
                )}
              </div>

              {/* Missing Skills */}
              <div className="p-4 rounded-xl bg-amber-950/10 border border-amber-500/10">
                <h4 className="text-xs font-semibold text-amber-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                  <AlertCircle className="w-4 h-4" /> Gaps ({selectedAnalysis.missing_skills.length})
                </h4>
                {selectedAnalysis.missing_skills.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {selectedAnalysis.missing_skills.map((skill) => (
                      <span key={skill} className="text-xs px-2.5 py-1 rounded-md bg-amber-950/20 text-amber-400 border border-amber-500/20 font-medium">
                        {skill}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-emerald-400 font-medium">Zero gaps! Excellent credentials match.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Roadmap Steps */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl">
        <h3 className="text-base font-bold text-slate-200 mb-3 flex items-center gap-2">
          <Cpu className="w-5 h-5 text-indigo-400" /> Actionable Step-by-Step Roadmap
        </h3>
        <p className="text-sm text-slate-400 mb-6">{data.roadmap.skill_gap_summary}</p>
        
        <div className="relative border-l border-slate-800 ml-4 space-y-6">
          {data.roadmap.steps.map((step, idx) => (
            <div key={idx} className="relative pl-7 group">
              <span className="absolute -left-3.5 top-0.5 w-7 h-7 rounded-full bg-slate-950 border-2 border-indigo-500/60 text-xs font-bold text-indigo-400 flex items-center justify-center transition-all group-hover:border-indigo-400 group-hover:scale-105">
                {idx + 1}
              </span>
              <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-900/60 transition-all hover:border-slate-800/80">
                <p className="text-sm text-slate-300 font-medium">{step}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Suggested Courses & Certifications */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Recommended Certifications */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl">
          <h3 className="text-base font-bold text-slate-200 mb-4 flex items-center gap-2">
            <Award className="w-5 h-5 text-indigo-400" /> Target Certifications
          </h3>
          <div className="space-y-3">
            {data.certifications.map((cert) => (
              <div key={cert} className="flex items-start gap-3 p-3.5 rounded-xl bg-slate-950/30 border border-slate-900">
                <Award className="w-5 h-5 text-indigo-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-semibold text-slate-300">{cert}</p>
                  <p className="text-xs text-slate-500 mt-0.5">Increases resume score weight by closing layout and metrics gaps.</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Suggested Courses */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl">
          <h3 className="text-base font-bold text-slate-200 mb-4 flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-indigo-400" /> Recommended Learning paths
          </h3>
          <div className="space-y-3">
            {data.courses.map((course) => (
              <div key={course} className="flex items-start gap-3 p-3.5 rounded-xl bg-slate-950/30 border border-slate-900">
                <BookOpen className="w-5 h-5 text-violet-500 flex-shrink-0 mt-0.5" />
                <div className="flex-grow">
                  <p className="text-sm font-semibold text-slate-300">{course}</p>
                  <p className="text-xs text-slate-500 mt-0.5">Focuses on technical missing criteria identified above.</p>
                </div>
                <a
                  href={`https://www.google.com/search?q=${encodeURIComponent(course)}`}
                  target="_blank"
                  rel="noreferrer"
                  className="p-1.5 rounded-lg bg-slate-900 text-slate-400 hover:text-slate-200 hover:bg-slate-850 self-center"
                >
                  <ChevronRight className="w-4 h-4" />
                </a>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
