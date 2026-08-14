/**
 * Store d'état d'authentification global. Volontairement en mémoire (React
 * state via Zustand) — jamais de token en localStorage/sessionStorage, qui
 * seraient exposés à toute injection XSS. Un refresh de page reconnecte
 * silencieusement via un cookie httpOnly côté backend (à finaliser en prod ;
 * en dev, la session est perdue au reload, ce qui est acceptable pour l'Epic 1).
 */
import { create } from "zustand";

import { apiClient, setTokens } from "../../api/client";

export interface AuthUser {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  cooperative_id: string | null;
  /** Modules métier accessibles au rôle (RBAC), pour afficher/masquer le sidebar. */
  modules: string[];
}

interface AuthState {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

let currentRefreshToken: string | null = null;

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const { data } = await apiClient.post("/auth/login/", { email, password });
      setTokens({ access: data.access, refresh: data.refresh });
      currentRefreshToken = data.refresh;
      set({ user: data.user, isAuthenticated: true, isLoading: false });
    } catch {
      set({
        isLoading: false,
        error: "Email ou mot de passe incorrect.",
      });
      throw new Error("login_failed");
    }
  },

  logout: async () => {
    try {
      if (currentRefreshToken) {
        await apiClient.post("/auth/logout/", { refresh: currentRefreshToken });
      }
    } finally {
      setTokens(null);
      currentRefreshToken = null;
      set({ user: null, isAuthenticated: false });
    }
  },
}));
