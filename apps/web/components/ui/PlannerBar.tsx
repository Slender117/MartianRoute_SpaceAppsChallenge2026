"use client";

import Link from "next/link";

import { LanguageToggle } from "@/components/ui/LanguageToggle";
import { LivePanel } from "@/components/ui/LivePanel";
import { useT } from "@/lib/i18n";

/** Barra de arriba al centro: regreso a la portada, idioma y "Marte hoy". */
export function PlannerBar() {
  const t = useT();
  return (
    <header className="planner-bar">
      <Link href="/" className="planner-home" title={t.homeTitle} aria-label={t.homeTitle}>
        <span aria-hidden>←</span> <span className="planner-brand">Martian Route</span>
      </Link>
      <LanguageToggle />
      <LivePanel />
    </header>
  );
}
