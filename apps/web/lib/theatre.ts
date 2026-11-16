import { getProject } from "@theatre/core";

// Cinematic sequence of the demo (globe → Jezero → route → comparison with Perseverance).
// To edit it visually, import @theatre/studio only in development and export the
// state to demo-state.json; then pass it here with getProject("WazeMars", { state }).
export const demoProject = getProject("WazeMars");
export const demoSheet = demoProject.sheet("Demo");
