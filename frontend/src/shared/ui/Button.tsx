import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "danger" | "ghost" | "accent";

const VARIANT_CLASSES: Record<Variant, string> = {
  primary: "bg-moss-700 text-white hover:bg-moss-800 focus:ring-moss-600/40",
  accent: "bg-ochre-500 text-ink-950 hover:bg-ochre-600 focus:ring-ochre-500/40",
  secondary: "border border-ink-900/15 bg-white text-ink-800 hover:border-ink-900/25 hover:bg-sand-50 focus:ring-moss-600/20",
  danger: "border border-terracotta-500/30 bg-terracotta-500/10 text-terracotta-700 hover:bg-terracotta-500/20 focus:ring-terracotta-500/30",
  ghost: "text-ink-700 hover:bg-sand-100 focus:ring-moss-600/20",
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
