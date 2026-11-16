"use client";

import { useEffect } from "react";

import { useLang, type Lang } from "@/lib/i18n";

const OPTIONS: { id: Lang; label: string; title: string }[] = [
  { id: "es", label: "ES", title: "Español" },
  { id: "en", label: "EN", title: "English" },
];

/** ES / EN buttons in the top bar. The chosen language is remembered in the browser. */
export function LanguageToggle() {
  const lang = useLang((s) => s.lang);
  const setLang = useLang((s) => s.setLang);
  const restore = useLang((s) => s.restore);

  // If the user picked Spanish on another visit, it is applied on load.
  useEffect(restore, [restore]);

  return (
    <div className="lang-toggle" role="group" aria-label="Idioma / Language">
      {OPTIONS.map((o) => (
        <button
          key={o.id}
          className={o.id === lang ? undefined : "ghost"}
          aria-pressed={o.id === lang}
          title={o.title}
          onClick={() => setLang(o.id)}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}
