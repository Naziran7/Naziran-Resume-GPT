import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { api } from "../lib/api";
import { User, Shield, Key, AlertTriangle, ArrowLeft, CheckCircle2 } from "lucide-react";
import { Link } from "react-router-dom";

export const Profile: React.FC = () => {
  const { user, logout } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleLogoutEverywhere = async () => {
    if (!confirm("Are you sure you want to sign out of all active devices? This will invalidate all your sessions.")) {
      return;
    }
    
    setIsSubmitting(true);
    setSuccessMsg(null);
    setErrorMsg(null);

    try {
      await api.post("/auth/logout-all");
      setSuccessMsg("Successfully signed out of all devices. Redirecting...");
      setTimeout(() => {
        logout(); // clear tokens and redirect to login
      }, 2000);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to log out of all devices.");
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col p-6">
      <div className="max-w-2xl mx-auto w-full space-y-8">
        
        {/* Back navigation */}
        <Link to="/" className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Dashboard</span>
        </Link>

        {/* Header branding */}
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Account Settings</h1>
          <p className="text-slate-400 text-sm mt-1">Manage your profile, credentials, and active sessions.</p>
        </div>

        {successMsg && (
          <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        {errorMsg && (
          <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive-foreground text-sm flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Profile Card */}
        <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-6">
          <div className="flex items-center gap-4 border-b border-border pb-6">
            <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center text-primary">
              <User className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">{user?.full_name || "Resume Candidate"}</h2>
              <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-primary mt-1 px-2.5 py-0.5 rounded-full bg-primary/10 border border-primary/20 uppercase tracking-wider">
                <Shield className="w-3 h-3" />
                {user?.role?.name || "User"}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-1">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Email Address</span>
              <p className="text-sm text-white font-medium">{user?.email}</p>
            </div>
            <div className="space-y-1">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Account Created</span>
              <p className="text-sm text-white font-medium">
                {user?.created_at ? new Date(user.created_at).toLocaleDateString() : "N/A"}
              </p>
            </div>
          </div>
        </div>

        {/* Security & Access Section */}
        <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-6">
          <h3 className="text-md font-bold text-white flex items-center gap-2">
            <Key className="w-5 h-5 text-primary" />
            Session Security
          </h3>
          <p className="text-xs text-slate-400">
            If you suspect unauthorized access to your account, you can terminate all other active logged-in sessions across all mobile or desktop browsers immediately.
          </p>

          <button
            onClick={handleLogoutEverywhere}
            disabled={isSubmitting}
            className="px-4 py-2 bg-destructive/10 border border-destructive/35 hover:bg-destructive/20 text-destructive-foreground text-xs font-bold rounded-lg transition-all"
          >
            {isSubmitting ? "Processing..." : "Sign Out of All Devices"}
          </button>
        </div>

      </div>
    </div>
  );
};
