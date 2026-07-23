import axios from "axios";

// Base API URL targeting the FastAPI backend (ensuring /api/v1 prefix)
const getApiBaseUrl = (): string => {
  let url = (import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1").trim().replace(/\/+$/, "");
  if (!url.endsWith("/api/v1")) {
    url = `${url}/api/v1`;
  }
  return url;
};

export const API_BASE_URL = getApiBaseUrl();

export const api = axios.create({
  baseURL: API_BASE_URL,
});

// Helper to manage JWT credentials in local storage
export const getAccessToken = () => localStorage.getItem("access_token");
export const getRefreshToken = () => localStorage.getItem("refresh_token");
export const setTokens = (accessToken: string, refreshToken: string) => {
  localStorage.setItem("access_token", accessToken);
  localStorage.setItem("refresh_token", refreshToken);
};
export const clearTokens = () => {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
};

// Request Interceptor: Attach bearer tokens dynamically
api.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Seamless access token refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Check if error is 401 and we haven't already retried this request
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = getRefreshToken();
      
      if (refreshToken) {
        try {
          // Call the refresh endpoint directly to avoid request interceptor looping
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          
          const { access_token, refresh_token: newRefreshToken } = response.data;
          setTokens(access_token, newRefreshToken);
          
          // Update the original request's authorization header and retry
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        } catch (refreshError) {
          // Refresh token is expired or revoked. Wipe local tokens and force signout
          clearTokens();
          window.location.href = "/login?session_expired=true";
          return Promise.reject(refreshError);
        }
      }
    }
    
    // Format error messages nicely
    const message = error.response?.data?.error?.message || error.message || "An unexpected error occurred.";
    return Promise.reject(new Error(message));
  }
);
