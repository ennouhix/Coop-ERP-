import { AlertCircle, CheckCircle2, X } from "lucide-react";

export interface ToastItem {
  id: number;
  kind: "success" | "error";
  message: string;
}

interface ToastStackProps {
  toasts: ToastItem[];
  onDismiss: (id: number) => void;
}

/** Pile de toasts (succès / erreur), fixée en haut à droite (haut à gauche en RTL). */
export function ToastStack({ toasts, onDismiss }: ToastStackProps) {
  if (toasts.length === 0) return null;

  return (
    <div className="pointer-events-none fixed inset-x-0 top-4 z-50 flex flex-col items-center gap-2 px-4">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          role="status"
          className={`pointer-events-auto flex w-full max-w-md items-start gap-3 rounded-md border px-4 py-3 shadow-card backdrop-blur-sm ${
            toast.kind === "success"
              ? "border-sage-300 bg-sage-50/95 text-sage-800"
              : "border-terracotta-300 bg-terracotta-50/95 text-terracotta-800"
          }`}
        >
          {toast.kind === "success" ? (
            <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-sage-600" />
          ) : (
            <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-terracotta-600" />
          )}
          <p className="flex-1 text-sm font-medium">{toast.message}</p>
          <button
            type="button"
            onClick={() => onDismiss(toast.id)}
            className="shrink-0 rounded p-0.5 transition hover:bg-ink-900/10"
            aria-label="Fermer"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      ))}
    </div>
  );
}
