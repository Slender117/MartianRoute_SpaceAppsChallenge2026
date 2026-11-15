"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useEffect } from "react";

import { useLang, type Lang } from "@/lib/i18n";
import { LANDING, REPO_URL } from "@/lib/landing";

// three.js necesita el navegador: el planeta no se renderiza en el servidor.
const MarsHero = dynamic(() => import("@/components/landing/MarsHero"), { ssr: false });

const LANGS: Lang[] = ["es", "en"];

/** Portada: Marte girando, secciones al hacer scroll y el botón Start fijo que abre el planificador. */
export default function Landing() {
  const lang = useLang((s) => s.lang);
  const setLang = useLang((s) => s.setLang);
  const restore = useLang((s) => s.restore);
  const t = LANDING[lang];

  useEffect(restore, [restore]);

  return (
    <div className="landing">
      <header className="landing-nav">
        <a href="#top" className="landing-brand">
          Martian Route
        </a>
        <nav aria-label={lang === "es" ? "Secciones" : "Sections"}>
          <a href="#about">{t.nav.about}</a>
          <a href="#project">{t.nav.project}</a>
          <a href="#data">{t.nav.data}</a>
          <a href="#team">{t.nav.team}</a>
          <a href={REPO_URL} target="_blank" rel="noreferrer">
            {t.nav.repo} ↗
          </a>
        </nav>
        <div className="landing-lang" role="group" aria-label="Idioma / Language">
          {LANGS.map((l) => (
            <button key={l} aria-pressed={l === lang} onClick={() => setLang(l)}>
              {l.toUpperCase()}
            </button>
          ))}
        </div>
      </header>

      <main className="landing-main">
        <section id="top" className="landing-hero">
          <div className="landing-planet">
            <MarsHero />
          </div>
          <div className="landing-hero-text">
            <p className="landing-kicker">{t.heroKicker}</p>
            <h1>{t.heroTitle}</h1>
            <p>{t.heroText}</p>
          </div>
          <a href="#about" className="landing-scroll">
            {t.scrollHint} ↓
          </a>
        </section>

        <section id="about" className="landing-section">
          <h2>{t.aboutTitle}</h2>
          {t.aboutText.map((p) => (
            <p key={p}>{p}</p>
          ))}
        </section>

        <section id="project" className="landing-section">
          <h2>{t.projectTitle}</h2>
          <div className="landing-grid">
            {t.projectCards.map((c) => (
              <article key={c.title} className="landing-card">
                <h3>{c.title}</h3>
                <p>{c.text}</p>
              </article>
            ))}
          </div>
        </section>

        <section id="data" className="landing-section">
          <h2>{t.dataTitle}</h2>
          <p className="muted">{t.dataIntro}</p>
          <dl className="landing-data">
            {t.dataRows.map(([layer, source]) => (
              <div key={layer}>
                <dt>{layer}</dt>
                <dd>{source}</dd>
              </div>
            ))}
          </dl>
        </section>

        <section id="team" className="landing-section">
          <h2>{t.teamTitle}</h2>
          <ul className="landing-grid landing-team">
            {t.team.map(([name, role]) => (
              <li key={name} className="landing-card">
                <h3>{name}</h3>
                <p>{role}</p>
              </li>
            ))}
          </ul>
        </section>

        <section id="repo" className="landing-section">
          <h2>{t.repoTitle}</h2>
          <p>{t.repoText}</p>
          <p className="landing-links">
            <a href={REPO_URL} target="_blank" rel="noreferrer">
              {t.repoButton} ↗
            </a>
            <a href={`${REPO_URL}/blob/main/docs/creditos.md`} target="_blank" rel="noreferrer">
              {t.creditsButton} ↗
            </a>
          </p>
        </section>

        <footer className="landing-footer muted">{t.footer}</footer>
      </main>

      <Link href="/planner" className="landing-start" title={t.startTitle}>
        {t.start} →
      </Link>
    </div>
  );
}
