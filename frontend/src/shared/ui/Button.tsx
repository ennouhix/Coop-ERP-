import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "danger" | "ghost";

const VARIANT_CLASSES: Record<Variant, string> = {
  primary: "bg-moss-600 text-white hover:bg-moss-700 focus:ring-moss-500/40",
  secondary: "bg-white text-ink-800 border border-ink-900/15 hover:bg-sand-100 focus:ring-moss-500/20",
  danger: "bg-white text-terracotta-600 border border-terracotta-500/30 hover:bg-terracotta-500/10 focus:ring-terracotta-500/30",
  ghost: "text-ink-700 hover:bg-sand-100 focus:ring-moss-500/20",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

export function Button({ variant = "primary", className = "", ...props }: ButtonProps) {
  return (
    <button
      className={[
        "inline-flex items-center gap-1.5 rounded-md px-3.5 py-2 text-sm font-semibold transition",
        "focus:outline-none focus:ring-2 disabled:cursor-not-allowed disabled:opacity-50",
        VARIANT_CLASSES[variant],
        className,
      ].join(" ")}
      {...props}
    />
  );
}
