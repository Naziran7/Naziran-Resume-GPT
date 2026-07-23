import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-background text-foreground">
        <div className="relative flex items-center justify-center">
          {/* Pulsing glow background effect */}
          <div className="absolute w-24 h-24 bg-primary/20 rounded-full blur-xl animate-pulse"></div>
          {/* Animated spinner rings */}
          <div className="w-12 h-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
        </div>
        <p className="mt-4 text-sm font-medium text-muted-foreground tracking-wider uppercase animate-pulse">
          Restoring Session...
        </p>
      </div>
    );
  }

  if (!isAuthenticated) {
    // Redirect to login, preserving the user's requested page location
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};
