type Tone = "moss" | "ochre" | "terracotta" | "neutral";

const TONE_CLASSES: Record<Tone, string> = {
  moss: "bg-moss-100 text-moss-700",
  ochre: "bg-ochre-100 text-ochre-600",
  terracotta: "bg-terracotta-500/10 text-terracotta-600",
  neutral: "bg-sand-100 text-ink-700",
};

export function StatusBadge({ label, tone = "neutral" }: { label: string; tone?: Tone }) {
  return (
    <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${TONE_CLASSES[tone]}`}>
      {label}
    </span>
  );
}
