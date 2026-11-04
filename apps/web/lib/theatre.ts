import { getProject } from "@theatre/core";

// Secuencia cinemática de la demo (globo → Jezero → ruta → comparación con Perseverance).
// Para editarla visualmente, importar @theatre/studio solo en desarrollo y exportar el
// estado a demo-state.json; luego pasarlo aquí con getProject("WazeMars", { state }).
export const demoProject = getProject("WazeMars");
export const demoSheet = demoProject.sheet("Demo");
