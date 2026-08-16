import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Link, Navigate } from "react-router-dom";
import {
  BarChart3,
  Calculator,
  CheckCircle2,
  Globe2,
  MailCheck,
  PackageSearch,
  Quote,
  Receipt,
  RefreshCw,
  Rocket,
  ShoppingCart,
  Sparkles,
  TrendingUp,
  UserPlus,
  Users,
} from "lucide-react";

import { Logo } from "../../shared/ui/Logo";
import { ZelligePattern } from "../../shared/ui/ZelligePattern";
import { useAuthStore } from "../auth/authStore";
import { Reveal } from "./Reveal";

function SectionHeading({
  eyebrow,
  title,
  subtitle,
}: {
  eyebrow: string;
  title: string;
  subtitle: string;
}) {
  return (
    <div className="mx-auto mb-12 max-w-2xl text-center">
      <Reveal>
        <p className="mb-3 inline-flex items-center gap-2 rounded-full border border-ochre-500/30 bg-ochre-500/10 px-4 py-1.5 font-mono text-[11px] uppercase tracking-eyebrow text-ochre-400">
          <Sparkles className="h-3.5 w-3.5" />
          {eyebrow}
        </p>
      </Reveal>
      <Reveal delay={90}>
        <h2 className="font-display text-3xl font-extrabold leading-tight tracking-tight text-white sm:text-4xl">
          {title}
        </h2>
      </Reveal>
      <Reveal delay={180}>
        <p className="mt-4 text-base leading-relaxed text-indigo-200">{subtitle}</p>
      </Reveal>
    </div>
  );
}

function KpiCard({ label, value, trend }: { label: string; value: string; trend?: string }) {
  return (
    <div className="rounded-lg border border-white/5 bg-white/5 p-3">
      <p className="font-mono text-[10px] uppercase tracking-widest text-indigo-300">{label}</p>
      <p className="mt-1 font-display text-lg font-extrabold text-white">{value}</p>
      {trend && (
        <span className="mt-1 inline-flex items-center gap-1 rounded-full bg-sage-500/15 px-1.5 py-0.5 text-[10px] font-semibold text-sage-300">
          <TrendingUp className="h-3 w-3" />
          {trend}
        </span>
      )}
    </div>
  );
}

function DashboardMock() {
  const { t } = useTranslation();
  const bars = [
    { h: "h-10", c: "bg-moss-400/80", d: "0ms" },
    { h: "h-16", c: "bg-ochre-400/80", d: "80ms" },
    { h: "h-8", c: "bg-terracotta-400/70", d: "160ms" },
    { h: "h-20", c: "bg-moss-400/80", d: "240ms" },
    { h: "h-12", c: "bg-ochre-400/80", d: "320ms" },
    { h: "h-24", c: "bg-moss-400/80", d: "400ms" },
    { h: "h-14", c: "bg-terracotta-400/70", d: "480ms" },
    { h: "h-[4.5rem]", c: "bg-ochre-400/80", d: "560ms" },
    { h: "h-10", c: "bg-moss-400/80", d: "640ms" },
    { h: "h-16", c: "bg-ochre-400/80", d: "720ms" },
  ];

  return (
    <div className="relative mx-auto mt-16 max-w-3xl animate-fade-up" style={{ animationDelay: "520ms" }}>
      <div
        aria-hidden="true"
        className="absolute -inset-10 rounded-full bg-ochre-500/20 blur-[110px]"
      />
      <div className="absolute left-1/2 top-0 hidden -translate-x-1/2 font-display text-7xl font-extrabold tracking-tight text-white/[0.03] lg:block">
        COOP ERP
      </div>

      <div className="relative rounded-2xl border border-white/10 bg-indigo-900/80 p-3 shadow-2xl backdrop-blur-sm transition-transform duration-500 lg:rotate-2 lg:hover:rotate-0">
        <div className="flex items-center gap-2 px-2 pb-3">
          <span className="h-2.5 w-2.5 rounded-full bg-terracotta-400/80" />
          <span className="h-2.5 w-2.5 rounded-full bg-ochre-400/80" />
          <span className="h-2.5 w-2.5 rounded-full bg-sage-400/80" />
          <span className="ms-3 hidden flex-1 rounded-md border border-white/10 bg-indigo-950/60 px-3 py-1 text-[11px] text-indigo-300 sm:block">
            app.cooperp.ma
          </span>
          <span className="ms-auto flex h-6 w-6 items-center justify-center rounded-full bg-ochre-500 text-indigo-950">
            <Logo className="h-3.5 w-3.5" />
          </span>
        </div>

        <div className="rounded-xl bg-indigo-950 p-5">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <KpiCard label={t("landing.mock.kpi_members")} value="128" trend={t("landing.mock.trend_up")} />
            <KpiCard label={t("landing.mock.kpi_invoices")} value="42" trend={t("landing.mock.trend_up")} />
            <KpiCard label={t("landing.mock.kpi_stock")} value="96 %" trend={t("landing.mock.trend_ok")} />
            <KpiCard label={t("landing.mock.kpi_revenue")} value="48 500 MAD" trend={t("landing.mock.trend_up")} />
          </div>

          <div className="mt-3 rounded-lg border border-white/5 bg-white/5 p-4">
            <div className="mb-3 flex items-center justify-between">
              <p className="font-mono text-[10px] uppercase tracking-widest text-indigo-300">
                {t("landing.mock.sales")}
              </p>
              <div className="flex items-center gap-3">
                <span className="inline-flex items-center gap-1.5 text-[10px] text-indigo-300">
                  <span className="h-1.5 w-1.5 rounded-full bg-moss-400" />
                  {t("landing.mock.sales")}
                </span>
                <span className="inline-flex items-center gap-1.5 text-[10px] text-indigo-300">
                  <span className="h-1.5 w-1.5 rounded-full bg-ochre-400" />
                  {t("landing.mock.purchases")}
                </span>
              </div>
            </div>
            <div className="flex h-24 origin-bottom items-end gap-1.5">
              {bars.map((bar, index) => (
                <div
                  key={index}
                  className={`${bar.h} ${bar.c} flex-1 animate-grow origin-bottom rounded-t-sm`}
                  style={{ animationDelay: bar.d }}
                />
              ))}
            </div>
          </div>

          <div className="mt-3 divide-y divide-white/5 overflow-hidden rounded-lg border border-white/5 bg-white/5">
            {[
              { name: "A. Benali", invoice: "FAC-00012", status: t("landing.mock.paid"), ok: true },
              { name: "K. Idrissi", invoice: "FAC-00013", status: t("landing.mock.pending"), ok: false },
              { name: "Coop. Tiznit", invoice: "FAC-00014", status: t("landing.mock.paid"), ok: true },
            ].map((row) => (
              <div key={row.invoice} className="flex items-center justify-between px-4 py-2.5">
                <div className="flex items-center gap-3">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-white/10 text-[10px] font-bold text-white">
                    {row.name.charAt(0)}
                  </span>
                  <span className="text-xs text-indigo-100">{row.name}</span>
                  <span className="font-mono text-[10px] text-indigo-400">{row.invoice}</span>
                </div>
                <span
                  className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                    row.ok ? "bg-sage-500/15 text-sage-300" : "bg-ochre-500/15 text-ochre-300"
                  }`}
                >
                  {row.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="absolute -start-6 top-16 hidden animate-float items-center gap-2 rounded-lg border border-white/10 bg-indigo-900/90 px-3 py-2 shadow-lift lg:flex">
        <CheckCircle2 className="h-4 w-4 text-sage-300" />
        <span className="text-xs font-semibold text-white">{t("landing.mock.chip_stock")}</span>
      </div>
      <div className="absolute -end-8 top-6 hidden animate-float items-center gap-2 rounded-lg border border-white/10 bg-indigo-900/90 px-3 py-2 shadow-lift lg:flex" style={{ animationDelay: "1.2s" }}>
        <Globe2 className="h-4 w-4 text-ochre-300" />
        <span className="text-xs font-semibold text-white">{t("landing.mock.chip_lang")}</span>
      </div>
      <div
        className="absolute -bottom-5 start-1/4 hidden animate-float items-center gap-2 rounded-lg border border-white/10 bg-indigo-900/90 px-3 py-2 shadow-lift lg:flex"
        style={{ animationDelay: "2.1s" }}
      >
        <RefreshCw className="h-4 w-4 text-terracotta-300" />
        <span className="text-xs font-semibold text-white">{t("landing.mock.chip_sync")}</span>
      </div>
    </div>
  );
}

function Hero() {
  const { t } = useTranslation();
  return (
    <section className="relative overflow-hidden">
      <div
        aria-hidden="true"
        className="absolute -top-48 left-1/2 h-[540px] w-[900px] -translate-x-1/2 rounded-full bg-ochre-500/15 blur-[130px]"
      />
      <div
        aria-hidden="true"
        className="absolute -start-40 top-40 h-80 w-80 rounded-full bg-moss-500/15 blur-[110px]"
      />
      <div
        aria-hidden="true"
        className="absolute -end-40 top-72 h-80 w-80 rounded-full bg-aubergine-500/15 blur-[110px]"
      />

      <div aria-hidden="true" className="absolute start-16 top-32 hidden h-16 w-16 rotate-12 rounded-xl border border-ochre-500/40 lg:block animate-float-rotate" />
      <div
        aria-hidden="true"
        className="absolute end-24 top-56 hidden h-10 w-10 rounded-full border border-sage-400/40 lg:block animate-float"
        style={{ animationDelay: "1.5s" }}
      />
      <div
        aria-hidden="true"
        className="absolute start-1/3 bottom-24 hidden h-8 w-8 rounded-lg border border-terracotta-400/40 lg:block animate-float"
        style={{ animationDelay: "0.8s" }}
      />

      <div className="relative mx-auto max-w-3xl px-4 pb-10 pt-16 text-center sm:pt-24">
        <div className="animate-fade-up">
          <p className="mx-auto inline-flex items-center gap-2 rounded-full border border-ochre-500/30 bg-ochre-500/10 px-4 py-1.5 font-mono text-[11px] uppercase tracking-eyebrow text-ochre-400">
            <span className="h-1.5 w-1.5 animate-pulse-dot rounded-full bg-ochre-400" />
            {t("landing.hero_badge")}
          </p>
        </div>

        <h1
          className="mt-6 font-display text-4xl font-extrabold leading-[1.08] tracking-tight text-white sm:text-6xl animate-fade-up"
          style={{ animationDelay: "100ms" }}
        >
          {t("landing.hero_title_1")}{" "}
          <span className="bg-gradient-to-r from-ochre-300 via-terracotta-300 to-ochre-400 bg-clip-text text-transparent animate-gradient-x bg-[length:200%_auto]">
            {t("landing.hero_title_2")}
          </span>
        </h1>

        <p
          className="mx-auto mt-6 max-w-xl text-base leading-relaxed text-indigo-200 sm:text-lg animate-fade-up"
          style={{ animationDelay: "200ms" }}
        >
          {t("landing.hero_subtitle")}
        </p>

        <div
          className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row animate-fade-up"
          style={{ animationDelay: "300ms" }}
        >
          <Link
            to="/register"
            className="group relative inline-flex w-full items-center justify-center gap-2 overflow-hidden rounded-md bg-ochre-500 px-7 py-3.5 text-sm font-bold text-indigo-950 shadow-lift transition hover:bg-ochre-600 sm:w-auto"
          >
            <Sparkles className="h-4 w-4 transition-transform group-hover:rotate-12" />
            {t("landing.hero_cta_start")}
          </Link>
          <Link
            to="/login"
            className="inline-flex w-full items-center justify-center gap-2 rounded-md border border-white/15 bg-white/5 px-7 py-3.5 text-sm font-semibold text-white backdrop-blur-sm transition hover:bg-white/10 sm:w-auto"
          >
            {t("landing.hero_cta_login")}
          </Link>
        </div>

        <p
          className="mt-5 text-xs text-indigo-300 animate-fade-up"
          style={{ animationDelay: "400ms" }}
        >
          {t("landing.hero_hint")}
        </p>

        <DashboardMock />
      </div>
    </section>
  );
}

function Stats() {
  const { t } = useTranslation();
  const stats = [
    { value: t("landing.stat1_value"), label: t("landing.stat1_label") },
    { value: t("landing.stat2_value"), label: t("landing.stat2_label") },
    { value: t("landing.stat3_value"), label: t("landing.stat3_label") },
    { value: t("landing.stat4_value"), label: t("landing.stat4_label") },
  ];

  return (
    <section className="relative border-y border-white/5 bg-white/[0.02]">
      <div className="mx-auto grid max-w-6xl grid-cols-2 gap-8 px-4 py-14 lg:grid-cols-4">
        {stats.map((stat, index) => (
          <Reveal key={stat.label} delay={index * 90} className="text-center">
            <p className="font-display text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
              <span className="bg-gradient-to-r from-ochre-300 to-terracotta-300 bg-clip-text text-transparent">
                {stat.value}
              </span>
            </p>
            <p className="mt-2 text-sm text-indigo-300">{stat.label}</p>
          </Reveal>
        ))}
      </div>
    </section>
  );
}

function FeatureCard({
  icon,
  title,
  description,
  chip,
}: {
  icon: ReactNode;
  title: string;
  description: string;
  chip: string;
}) {
  return (
    <Reveal className="h-full lg:col-span-3">
      <div className="group relative h-full overflow-hidden rounded-xl border border-white/10 bg-white/[0.04] p-6 transition-all duration-300 hover:-translate-y-1 hover:border-ochre-500/40 hover:bg-white/[0.07]">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -end-16 -top-16 h-40 w-40 rounded-full bg-ochre-500/10 blur-3xl opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        />
        <div className="flex items-center justify-between">
          <span className="flex h-11 w-11 items-center justify-center rounded-lg bg-ochre-500/15 text-ochre-400 transition-colors duration-300 group-hover:bg-ochre-500 group-hover:text-indigo-950">
            {icon}
          </span>
          <span className="rounded-full border border-white/10 px-2.5 py-1 font-mono text-[10px] uppercase tracking-wider text-indigo-300">
            {chip}
          </span>
        </div>
        <h3 className="mt-5 font-display text-lg font-bold text-white">{title}</h3>
        <p className="mt-2 text-sm leading-relaxed text-indigo-200">{description}</p>
      </div>
    </Reveal>
  );
}

function Features() {
  const { t } = useTranslation();
  return (
    <section className="relative mx-auto max-w-6xl px-4 py-24">
      <SectionHeading
        eyebrow={t("landing.features_eyebrow")}
        title={t("landing.features_title")}
        subtitle={t("landing.features_subtitle")}
      />
      <div className="grid gap-5 lg:grid-cols-6">
        <FeatureCard
          icon={<Users className="h-5 w-5" />}
          title={t("landing.feature1_title")}
          description={t("landing.feature1_desc")}
          chip={t("landing.feature1_chip")}
        />
        <FeatureCard
          icon={<Receipt className="h-5 w-5" />}
          title={t("landing.feature2_title")}
          description={t("landing.feature2_desc")}
          chip={t("landing.feature2_chip")}
        />
        <FeatureCard
          icon={<ShoppingCart className="h-5 w-5" />}
          title={t("landing.feature3_title")}
          description={t("landing.feature3_desc")}
          chip={t("landing.feature3_chip")}
        />
        <FeatureCard
          icon={<PackageSearch className="h-5 w-5" />}
          title={t("landing.feature4_title")}
          description={t("landing.feature4_desc")}
          chip={t("landing.feature4_chip")}
        />
        <FeatureCard
          icon={<Calculator className="h-5 w-5" />}
          title={t("landing.feature5_title")}
          description={t("landing.feature5_desc")}
          chip={t("landing.feature5_chip")}
        />
        <FeatureCard
          icon={<BarChart3 className="h-5 w-5" />}
          title={t("landing.feature6_title")}
          description={t("landing.feature6_desc")}
          chip={t("landing.feature6_chip")}
        />
      </div>
    </section>
  );
}

function Steps() {
  const { t } = useTranslation();
  const steps = [
    { icon: <UserPlus className="h-5 w-5" />, title: t("landing.step1_title"), desc: t("landing.step1_desc") },
    { icon: <MailCheck className="h-5 w-5" />, title: t("landing.step2_title"), desc: t("landing.step2_desc") },
    { icon: <Rocket className="h-5 w-5" />, title: t("landing.step3_title"), desc: t("landing.step3_desc") },
  ];

  return (
    <section className="relative border-t border-white/5 bg-white/[0.02] py-24">
      <div className="mx-auto max-w-5xl px-4">
        <Reveal>
          <h2 className="mb-14 text-center font-display text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
            {t("landing.steps_title")}
          </h2>
        </Reveal>

        <div className="relative grid gap-10 sm:grid-cols-3">
          <div
            aria-hidden="true"
            className="absolute left-[16%] right-[16%] top-7 hidden h-px bg-gradient-to-r from-transparent via-ochre-500/50 to-transparent sm:block"
          />
          {steps.map((step, index) => (
            <Reveal key={step.title} delay={index * 130} className="relative text-center">
              <div className="relative mx-auto flex h-14 w-14 items-center justify-center rounded-full border border-ochre-500/40 bg-indigo-900 text-ochre-400 shadow-lift">
                {step.icon}
              </div>
              <p className="mt-6 font-mono text-[11px] uppercase tracking-eyebrow text-ochre-400">
                {String(index + 1).padStart(2, "0")}
              </p>
              <h3 className="mt-2 font-display text-lg font-bold text-white">{step.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-indigo-200">{step.desc}</p>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

function Slogan() {
  const { t } = useTranslation();
  return (
    <section className="relative overflow-hidden border-t border-white/5 bg-white/[0.02] py-24">
      <div
        aria-hidden="true"
        className="absolute -top-24 left-1/2 h-48 w-[640px] -translate-x-1/2 rounded-full bg-ochre-500/10 blur-[100px]"
      />
      <div className="relative mx-auto max-w-4xl px-4 text-center">
        <Reveal>
          <Quote className="mx-auto h-10 w-10 rotate-180 text-ochre-500/40" />
        </Reveal>
        <Reveal delay={90}>
          <p className="mb-5 mt-2 inline-flex items-center gap-2 rounded-full border border-ochre-500/30 bg-ochre-500/10 px-4 py-1.5 font-mono text-[11px] uppercase tracking-eyebrow text-ochre-400">
            <Sparkles className="h-3.5 w-3.5" />
            {t("landing.slogan_eyebrow")}
          </p>
        </Reveal>
        <Reveal delay={180}>
          <h2 className="font-display text-4xl font-extrabold leading-[1.1] tracking-tight text-white sm:text-5xl">
            {t("landing.slogan_text")}
          </h2>
        </Reveal>
        <Reveal delay={260}>
          <p className="mx-auto mt-5 max-w-xl text-base text-indigo-200">
            {t("landing.slogan_note")}
          </p>
        </Reveal>
      </div>
    </section>
  );
}

function CtaBand() {
  const { t } = useTranslation();
  return (
    <section className="relative mx-auto max-w-6xl px-4 pb-24">
      <Reveal>
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-moss-700 via-ochre-700 to-terracotta-700 p-[1px] shadow-lift">
          <div className="relative overflow-hidden rounded-2xl bg-indigo-950/95 px-8 py-14 text-center sm:px-14">
            <div
              aria-hidden="true"
              className="absolute -top-24 left-1/2 h-64 w-[520px] -translate-x-1/2 rounded-full bg-ochre-500/25 blur-[90px]"
            />
            <div aria-hidden="true" className="absolute -bottom-10 start-1/4 h-32 w-32 rounded-full bg-moss-500/20 blur-[70px]" />

            <div className="relative">
              <h2 className="font-display text-3xl font-extrabold leading-tight tracking-tight text-white sm:text-4xl">
                {t("landing.cta_title")}
              </h2>
              <p className="mx-auto mt-4 max-w-lg text-sm leading-relaxed text-indigo-200">
                {t("landing.cta_subtitle")}
              </p>
              <div className="mt-8">
                <Link
                  to="/register"
                  className="group inline-flex items-center justify-center gap-2 rounded-md bg-ochre-500 px-8 py-4 text-sm font-bold text-indigo-950 shadow-lift transition hover:bg-ochre-600"
                >
                  <span className="h-1.5 w-1.5 animate-pulse-dot rounded-full bg-indigo-950" />
                  {t("landing.cta_button")}
                </Link>
              </div>
              <p className="mt-5 text-xs text-indigo-300">{t("landing.cta_note")}</p>
            </div>
          </div>
        </div>
      </Reveal>
    </section>
  );
}

export function LandingPage() {
  const { t } = useTranslation();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="relative min-h-screen bg-indigo-950">
      <ZelligePattern className="pointer-events-none absolute inset-0 h-full w-full text-ochre-500/[0.06]" />

      <div className="relative flex items-center justify-center gap-2 bg-gradient-to-r from-moss-700 via-ochre-600 to-terracotta-700 px-4 py-2 text-center text-xs font-semibold text-white">
        <Sparkles className="h-3.5 w-3.5" />
        {t("landing.announce")}
      </div>

      <header className="sticky top-0 z-40 border-b border-white/5 bg-indigo-950/70 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <Link to="/" className="flex items-center gap-2.5">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-ochre-500 text-indigo-950">
              <Logo className="h-5 w-5" />
            </span>
            <span className="font-display text-lg font-extrabold tracking-tight text-white">
              {t("app.name")}
            </span>
          </Link>

          <nav className="flex items-center gap-3">
            <Link
              to="/login"
              className="rounded-md px-3.5 py-2 text-sm font-semibold text-indigo-200 transition hover:text-white"
            >
              {t("landing.nav_login")}
            </Link>
            <Link
              to="/register"
              className="rounded-md bg-ochre-500 px-3.5 py-2 text-sm font-bold text-indigo-950 transition hover:bg-ochre-600"
            >
              {t("landing.nav_cta")}
            </Link>
          </nav>
        </div>
      </header>

      <main className="relative">
        <Hero />
        <Stats />
        <Features />
        <Steps />
        <Slogan />
        <CtaBand />
      </main>

      <footer className="relative border-t border-white/10 py-8">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-4 sm:flex-row">
          <div className="flex items-center gap-2">
            <span className="flex h-7 w-7 items-center justify-center rounded-md bg-ochre-500 text-indigo-950">
              <Logo className="h-4 w-4" />
            </span>
            <span className="text-sm font-semibold text-white">{t("app.name")}</span>
          </div>

          <nav className="flex items-center gap-4 text-sm">
            <Link to="/login" className="text-indigo-300 transition hover:text-white">
              {t("landing.footer_connect")}
            </Link>
            <Link to="/register" className="text-indigo-300 transition hover:text-white">
              {t("landing.footer_create")}
            </Link>
          </nav>

          <p className="text-xs text-indigo-300">
            © {new Date().getFullYear()} {t("app.name")} — {t("landing.footer_note")}
          </p>
        </div>
      </footer>
    </div>
  );
}
