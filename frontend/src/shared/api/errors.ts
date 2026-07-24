import type { AxiosError } from "axios";

/**
 * Le backend renvoie deux formats d'erreur selon les cas (voir
 * apps.core.exceptions côté Django) :
 * - {"error": {"message": "..."}}  (erreurs métier des services)
 * - {"field_name": ["message"]}    (erreurs de validation DRF standard)
 * Cette fonction gère les deux pour ne jamais afficher "[object Object]".
 */
export function extractApiErrorMessage(error: unknown, fallback: string): string {
  const axiosError = error as AxiosError<Record<string, unknown>>;
  const data = axiosError.response?.data;
  if (!data) return fallback;

  if (typeof data === "object" && "error" in data) {
    const nested = (data as { error?: { message?: string } }).error;
    if (nested?.message) return nested.message;
  }

  const firstFieldErrors = Object.values(data).find((v) => Array.isArray(v) && v.length > 0) as
    | string[]
    | undefined;
  if (firstFieldErrors) return firstFieldErrors[0];

  return fallback;
}
