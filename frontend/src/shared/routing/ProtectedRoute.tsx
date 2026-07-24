import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";

import { useAuthStore } from "../../features/auth/authStore";

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
