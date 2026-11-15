"use client";

import dynamic from "next/dynamic";
import Image from "next/image";
import Link from "next/link";
import { useEffect, useState } from "react";

import { useLang, type Lang } from "@/lib/i18n";
import { LANDING, REPO_URL } from "@/lib/landing";
import plannerShot from "@/public/img/planificador.webp";

// three.js necesita el navegador: el planeta no se renderiza en el servidor.
const MarsHero = dynamic(() => import("@/components/landing/MarsHero"), { ssr: false });

const LANGS: Lang[] = ["es", "en"];
const SECTIONS = ["about", "project", "data", "team"] as const;
type Section = (typeof SECTIONS)[number];

/** Sección que ocupa la mitad de la pantalla, para resaltarla en el menú. */
function useActiveSection(): Section | null {
  const [active, setActive] = useState<Section | null>(null);
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        for (const e of entries) if (e.isIntersecting) setActive(e.target.id as Section);
      },
      // Una franja delgada a media pantalla: solo una sección la cruza a la vez.
      { rootMargin: "-45% 0px -50% 0px" },
    );
    for (const id of [...SECTIONS, "top", "repo"]) {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    }
    return () => observer.disconnect();
  }, []);
  return active;
}

/** Portada: Marte girando, secciones al hacer scroll y el botón Start fijo que abre el planificador. */
export default function Landing() {
  const lang = useLang((s) => s.lang);
  const setLang = useLang((s) => s.setLang);
  const restore = useLang((s) => s.restore);
  const t = LANDING[lang];
  const active = useActiveSection();
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(restore, [restore]);

  return (
    <div className="landing">
      <header className="landing-nav">
        <a href="#top" className="landing-brand">
          <span className="landing-logo" aria-hidden />
          Martian Route
        </a>
        <nav id="landing-links" aria-label={t.sectionsLabel} className={menuOpen ? "is-open" : undefined}>
          {SECTIONS.map((id) => (
            <a
              key={id}
              href={`#${id}`}
              aria-current={active === id ? "location" : undefined}
              onClick={() => setMenuOpen(false)}
            >
              {t.nav[id]}
            </a>
          ))}
          <a href={REPO_URL} target="_blank" rel="noreferrer" onClick={() => setMenuOpen(false)}>
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
        <button
          className="landing-menu"
          aria-expanded={menuOpen}
          aria-controls="landing-links"
          aria-label={menuOpen ? t.menuClose : t.menuOpen}
          onClick={() => setMenuOpen(!menuOpen)}
        >
          <span aria-hidden>{menuOpen ? "✕" : "☰"}</span>
        </button>
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
          <figure className="landing-shot">
            <Image
              src={plannerShot}
              alt={t.shotAlt}
              sizes="(max-width: 1088px) calc(100vw - 48px), 1040px"
              placeholder="blur"
            />
            <figcaption className="muted">{t.shotCaption}</figcaption>
          </figure>
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
        {t.start} <span aria-hidden>→</span>
      </Link>
    </div>
  );
}
