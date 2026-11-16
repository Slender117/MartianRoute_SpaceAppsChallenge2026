import { useSyncExternalStore } from "react";

/**
 * true if the CSS query matches (for example "(max-width: 720px)"), and it updates when
 * the window is resized. On the server it is always false.
 */
export function useMediaQuery(query: string): boolean {
  return useSyncExternalStore(
    (onChange) => {
      const list = window.matchMedia(query);
      list.addEventListener("change", onChange);
      return () => list.removeEventListener("change", onChange);
    },
    () => window.matchMedia(query).matches,
    () => false,
  );
}
