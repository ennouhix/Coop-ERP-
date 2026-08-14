type Tone = "moss" | "ochre" | "terracotta" | "neutral";

const TONE_CLASSES: Record<Tone, { badge: string; dot: string }> = {
  moss: { badge: "bg-sage-50 text-sage-700 border-sage-200", dot: "bg-sage-500" },
  ochre: { badge: "bg-ochre-50 text-ochre-700 border-ochre-200", dot: "bg-ochre-500" },
  terracotta: { badge: "bg-terracotta-50 text-terracotta-700 border-terracotta-200", dot: "bg-terracotta-500" },
  neutral: { badge: "bg-sand-100 text-ink-700 border-ink-900/10", dot: "bg-ink-400" },
};

export function StatusBadge({ label, tone = "neutral" }: { label: string; tone?: Tone }) {
  const { badge, dot } = TONE_CLASSES[tone];
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium ${badge}`}>
      <span aria-hidden="true" className={`inline-block h-1.5 w-1.5 rounded-full ${dot}`} />
      {label}
    </span>
  );
}
