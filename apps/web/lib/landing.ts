// Textos de la portada (/) en español e inglés. TypeScript obliga a que `en` tenga las mismas claves.

import type { Lang } from "./i18n";

export const REPO_URL = "https://github.com/Slender117/SpaceAppsChallenge2026";

const es = {
  nav: { about: "Acerca de", project: "Proyecto", data: "Datos", team: "Equipo", repo: "Repositorio" },
  start: "Start",
  startTitle: "Abrir el planificador de rutas",
  menuOpen: "Abrir el menú",
  menuClose: "Cerrar el menú",
  sectionsLabel: "Secciones",
  heroKicker: "NASA Space Apps Challenge 2026",
  heroTitle: "Martian Route",
  heroText:
    "Planea una caminata en Marte: elige un punto de inicio y un destino, y compara rutas por pendiente, obstáculos, oxígeno y regreso seguro a la base.",
  scrollHint: "Desliza para conocer el proyecto",

  aboutTitle: "Acerca de",
  aboutText: [
    "Martian Route responde al reto Interplanetary Survival Guide: Martian Map. Las herramientas de mapas de Marte ya cubren lo regional y lo global; aquí el foco es la zona de una caminata, a escala de metros.",
    "La pregunta central: qué ruta de EVA a pie da más valor científico sin romper los límites de pendiente, autonomía del traje, dosis de radiación y regreso a la base.",
  ],

  projectTitle: "Cómo funciona",
  shotAlt:
    "El planificador en el cráter Jezero: la ruta de la base al destino de la demo sobre el relieve y la ortofoto de CTX, con el mapa de regreso seguro en verde, amarillo y rojo",
  shotCaption:
    "Captura del planificador con datos reales de Jezero: la ruta de la demo y el mapa de regreso seguro (verde: ida y vuelta dentro de la autonomía planeable).",
  projectCards: [
    {
      title: "Tres rutas y una referencia",
      text: "Segura, Rápida y Científica son pesos distintos sobre el mismo costo. La línea base, la ruta más corta que respeta la pendiente, sirve para comparar.",
    },
    {
      title: "Oxígeno y punto de no retorno",
      text: "Cada ruta trae su O₂ por persona, tiempo y dosis, y marca el punto desde el que el regreso ya no cabe en la autonomía planeable.",
    },
    {
      title: "Mapa de regreso seguro",
      text: "Colorea el terreno según los minutos que tomaría volver a la base desde cada punto.",
    },
    {
      title: "Marte hoy",
      text: "Eyecciones solares previstas para Marte (DONKI), y posición e imágenes recientes de Perseverance.",
    },
    {
      title: "Validado contra un rover",
      text: "Las rutas se comparan con el recorrido real de Perseverance en Jezero para ver si son creíbles.",
    },
    {
      title: "Dos sitios reales",
      text: "Cráter Jezero (CTX y HiRISE) y Gale, alrededor de Curiosity. La arquitectura sirve para cualquier región.",
    },
  ],

  dataTitle: "Datos de misiones de NASA",
  dataIntro: "Cada capa sale de un instrumento distinto; las fuentes y citas están en docs/creditos.md.",
  dataRows: [
    ["Pendiente", "MOLA / CTX / HiRISE (modelos de elevación)"],
    ["Obstáculos", "HiRISE"],
    ["Tipo de terreno", "NOAH-H"],
    ["Inercia térmica", "THEMIS"],
    ["Hielo subsuperficial", "SWIM"],
    ["Minerales", "CRISM"],
    ["Clima espacial", "DONKI (CCMC, WSA-ENLIL)"],
    ["Rover e imágenes", "Mars 2020 Perseverance"],
  ],

  teamTitle: "Equipo",
  team: [
    ["Tulio", "Pipeline de capas, infraestructura y despliegue"],
    ["Jairo", "Idea inicial del proyecto"],
    ["Miguel", "Backend y dirección del frontend"],
    ["Milton", "Componentes de interfaz"],
    ["Edgar", "Ciencia y validación"],
    ["Williams", "Pruebas de uso, demo y video"],
  ],

  repoTitle: "Repositorio",
  repoText: "El código, los datos crudos de las regiones y la documentación son abiertos.",
  repoButton: "Ver en GitHub",
  creditsButton: "Fuentes y créditos",

  footer: "Proyecto para NASA Space Apps Challenge 2026. No está respaldado por NASA.",
};

type LandingStrings = typeof es;

const en: LandingStrings = {
  nav: { about: "About", project: "Project", data: "Data", team: "Team", repo: "Repository" },
  start: "Start",
  startTitle: "Open the route planner",
  menuOpen: "Open the menu",
  menuClose: "Close the menu",
  sectionsLabel: "Sections",
  heroKicker: "NASA Space Apps Challenge 2026",
  heroTitle: "Martian Route",
  heroText:
    "Plan a walk on Mars: pick a start and a destination, and compare routes by slope, obstacles, oxygen and a safe return to base.",
  scrollHint: "Scroll to learn about the project",

  aboutTitle: "About",
  aboutText: [
    "Martian Route answers the Interplanetary Survival Guide: Martian Map challenge. Mars mapping tools already cover the regional and global scale; here the focus is the area of a single walk, at the scale of meters.",
    "The central question: which on-foot EVA route gives the most science without breaking the limits of slope, suit autonomy, radiation dose and return to base.",
  ],

  projectTitle: "How it works",
  shotAlt:
    "The planner at Jezero crater: the route from the base to the demo destination over the CTX terrain and orthophoto, with the safe-return map in green, yellow and red",
  shotCaption:
    "Screenshot of the planner with real Jezero data: the demo route and the safe-return map (green: round trip within the plannable autonomy).",
  projectCards: [
    {
      title: "Three routes and a reference",
      text: "Safe, Fast and Science are different weights on the same cost. The baseline, the shortest route that respects the slope, is the reference.",
    },
    {
      title: "Oxygen and point of no return",
      text: "Each route comes with its O₂ per person, time and dose, and marks the point after which the way back no longer fits in the plannable autonomy.",
    },
    {
      title: "Safe-return map",
      text: "Colors the terrain by the minutes it would take to get back to base from each point.",
    },
    {
      title: "Mars today",
      text: "Solar eruptions forecast to reach Mars (DONKI), plus Perseverance's position and latest images.",
    },
    {
      title: "Checked against a rover",
      text: "Routes are compared with Perseverance's real traverse in Jezero to see whether they are credible.",
    },
    {
      title: "Two real sites",
      text: "Jezero crater (CTX and HiRISE) and Gale, around Curiosity. The architecture works for any region.",
    },
  ],

  dataTitle: "Data from NASA missions",
  dataIntro: "Each layer comes from a different instrument; sources and citations are in docs/creditos.md.",
  dataRows: [
    ["Slope", "MOLA / CTX / HiRISE (elevation models)"],
    ["Obstacles", "HiRISE"],
    ["Terrain type", "NOAH-H"],
    ["Thermal inertia", "THEMIS"],
    ["Subsurface ice", "SWIM"],
    ["Minerals", "CRISM"],
    ["Space weather", "DONKI (CCMC, WSA-ENLIL)"],
    ["Rover and images", "Mars 2020 Perseverance"],
  ],

  teamTitle: "Team",
  team: [
    ["Tulio", "Layer pipeline, infrastructure and deployment"],
    ["Jairo", "Initial project idea"],
    ["Miguel", "Backend and frontend lead"],
    ["Milton", "Interface components"],
    ["Edgar", "Science and validation"],
    ["Williams", "User testing, demo and video"],
  ],

  repoTitle: "Repository",
  repoText: "The code, the raw data of the regions and the documentation are open.",
  repoButton: "View on GitHub",
  creditsButton: "Sources and credits",

  footer: "A project for the NASA Space Apps Challenge 2026. Not endorsed by NASA.",
};

export const LANDING: Record<Lang, LandingStrings> = { es, en };
