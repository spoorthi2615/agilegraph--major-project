import { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { apiClient } from '../api/client';
import type { UserProfile } from '../api/client';

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<UserProfile | null>(() => {
    try {
      const stored = localStorage.getItem("agilegraph_user");
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem("agilegraph_token");
  });

  const [loading, setLoading] = useState<boolean>(false);

  // Validate session on mount
  useEffect(() => {
    const validateToken = async () => {
      const storedToken = localStorage.getItem("agilegraph_token");
      if (!storedToken) {
        setUser(null);
        setToken(null);
        setLoading(false);
        return;
      }

      try {
        const profile = await apiClient.getMe();
        setUser(profile);
        setToken(storedToken);
        localStorage.setItem("agilegraph_user", JSON.stringify(profile));
      } catch (err) {
        console.warn("Session expired or invalid, clearing local auth state:", err);
        localStorage.removeItem("agilegraph_token");
        localStorage.removeItem("agilegraph_user");
        setUser(null);
        setToken(null);
      } finally {
        setLoading(false);
      }
    };

    validateToken();
  }, []);

  const login = async (username: string, password: string) => {
    setLoading(true);
    try {
      const res = await apiClient.login({ username, password });
      setToken(res.access_token);
      setUser(res.user);
      localStorage.setItem("agilegraph_token", res.access_token);
      localStorage.setItem("agilegraph_user", JSON.stringify(res.user));
    } finally {
      setLoading(false);
    }
  };

  const register = async (username: string, email: string, password: string) => {
    setLoading(true);
    try {
      const res = await apiClient.register({ username, email, password });
      setToken(res.access_token);
      setUser(res.user);
      localStorage.setItem("agilegraph_token", res.access_token);
      localStorage.setItem("agilegraph_user", JSON.stringify(res.user));
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      if (token) {
        await apiClient.logout();
      }
    } catch (e) {
      console.warn("Server logout notification failed:", e);
    } finally {
      setToken(null);
      setUser(null);
      localStorage.removeItem("agilegraph_token");
      localStorage.removeItem("agilegraph_user");
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token && !!user,
        loading,
        login,
        register,
        logout
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
