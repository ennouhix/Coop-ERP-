/**
 * Client HTTP central. Injecte automatiquement l'access token sur chaque
 * requête, et tente UN renouvellement automatique via le refresh token en
 * cas de 401 avant d'abandonner (évite de déconnecter l'utilisateur pour
 * un simple access token expiré en cours de session).
 */
import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export const apiClient = axios.create({ baseURL: API_BASE_URL });

/** Racine du serveur (sans /api/v1), pour construire les URLs de fichiers médias (logos, etc). */
const MEDIA_ORIGIN = API_BASE_URL.replace(/\/api\/v1\/?$/, "");

export function getMediaUrl(path: string | null | undefined): string | null {
  if (!path) return null;
  if (path.startsWith("http")) return path;
  return `${MEDIA_ORIGIN}${path.startsWith("/") ? "" : "/"}${path}`;
}

let accessToken: string | null = null;
let refreshToken: string | null = null;

export function setTokens(tokens: { access: string; refresh: string } | null) {
  accessToken = tokens?.access ?? null;
  refreshToken = tokens?.refresh ?? null;
}

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

let refreshPromise: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  if (!refreshToken) throw new Error("Aucun refresh token disponible.");
  const { data } = await axios.post(`${API_BASE_URL}/auth/refresh/`, { refresh: refreshToken });
  accessToken = data.access;
  return data.access as string;
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry && refreshToken) {
      originalRequest._retry = true;
      try {
        // Un seul refresh en vol même si plusieurs requêtes échouent en même temps.
        refreshPromise ??= refreshAccessToken().finally(() => {
          refreshPromise = null;
        });
        const newAccessToken = await refreshPromise;
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return apiClient(originalRequest);
      } catch {
        setTokens(null);
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);
