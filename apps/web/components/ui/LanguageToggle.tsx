"use client";

import { useEffect } from "react";

import { useLang, type Lang } from "@/lib/i18n";

const OPTIONS: { id: Lang; label: string; title: string }[] = [
  { id: "es", label: "ES", title: "Español" },
  { id: "en", label: "EN", title: "English" },
];

/** Botones ES / EN en la barra de arriba. El idioma elegido se recuerda en el navegador. */
export function LanguageToggle() {
  const lang = useLang((s) => s.lang);
  const setLang = useLang((s) => s.setLang);
  const restore = useLang((s) => s.restore);

  // Si el usuario eligió inglés en otra visita, se aplica al cargar.
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
