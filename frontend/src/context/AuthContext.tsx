import React, { createContext, useContext, useState, useEffect } from "react";
import { api, setTokens, clearTokens, getAccessToken } from "../lib/api";

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  role_id: string;
  role?: {
    id: string;
    name: string;
    description: string | null;
  } | null;
  created_at: string;
  updated_at: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: Record<string, string>) => Promise<void>;
  register: (payload: Record<string, string>) => Promise<void>;
  logout: () => Promise<void>;
  refetchUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchCurrentUser = async () => {
    try {
      const response = await api.get("/auth/me");
      setUser(response.data);
    } catch (error) {
      // Clear token if token is invalid or request fails
      clearTokens();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const token = getAccessToken();
    if (token) {
      fetchCurrentUser();
    } else {
      setIsLoading(false);
    }
  }, []);

  const login = async (credentials: Record<string, string>) => {
    setIsLoading(true);
    try {
      // Authenticate with JSON login endpoint
      const response = await api.post("/auth/login/json", credentials);
      const { access_token, refresh_token } = response.data;
      setTokens(access_token, refresh_token);
      await fetchCurrentUser();
    } catch (error) {
      setIsLoading(false);
      throw error;
    }
  };

  const register = async (payload: Record<string, string>) => {
    setIsLoading(true);
    try {
      await api.post("/auth/register", payload);
      // Automatically log in after registration
      await login({ email: payload.email, password: payload.password });
    } catch (error) {
      setIsLoading(false);
      throw error;
    }
  };

  const logout = async () => {
    setIsLoading(true);
    const refreshToken = localStorage.getItem("refresh_token");
    try {
      if (refreshToken) {
        await api.post("/auth/logout", { refresh_token: refreshToken });
      }
    } catch (error) {
      console.error("Failed to revoke session on server", error);
    } finally {
      clearTokens();
      setUser(null);
      setIsLoading(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
        refetchUser: fetchCurrentUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
