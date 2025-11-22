import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api-client";
import { clearAccessToken, getAccessToken, setAccessToken } from "@/lib/auth-storage";
import { ApiAuthResponse, ApiUser, ApiUserProfile } from "@/types/api";

interface AuthContextState {
  user: ApiUser | null;
  profile: ApiUserProfile | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<ApiAuthResponse>;
  registerUser: (payload: { email: string; password: string; full_name?: string | null }) => Promise<ApiUser>;
  logout: () => void;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextState | undefined>(undefined);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<ApiUser | null>(null);
  const [profile, setProfile] = useState<ApiUserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const bootstrap = async () => {
      const token = getAccessToken();
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const me = await api.getCurrentUser();
        setUser(me);
        const userProfile = await api.getProfile();
        setProfile(userProfile);
      } catch (error) {
        clearAccessToken();
      } finally {
        setLoading(false);
      }
    };
    void bootstrap();
  }, []);

  const login = async (email: string, password: string) => {
    const response = await api.login({ email, password });
    setAccessToken(response.access_token);
    setUser(response.user);
    try {
      const userProfile = await api.getProfile();
      setProfile(userProfile);
    } catch (error) {
      setProfile(null);
    }
    return response;
  };

  const registerUser = async (payload: { email: string; password: string; full_name?: string | null }) => {
    const created = await api.register(payload);
    return created;
  };

  const logout = () => {
    try {
      void api.logout();
    } catch (error) {
      // best effort: il backend registra un audit di logout se il token è valido
    }
    clearAccessToken();
    setUser(null);
    setProfile(null);
  };

  const refreshProfile = async () => {
    if (!user) return;
    const updated = await api.getProfile();
    setProfile(updated);
  };

  const value = useMemo(
    () => ({ user, profile, loading, login, registerUser, logout, refreshProfile }),
    [user, profile, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextState => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
};
