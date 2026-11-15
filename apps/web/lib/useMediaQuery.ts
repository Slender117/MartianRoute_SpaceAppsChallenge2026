import { useSyncExternalStore } from "react";

/**
 * true si la consulta de CSS se cumple (por ejemplo "(max-width: 720px)"), y se actualiza al
 * cambiar el tamaño de la ventana. En el servidor siempre es false.
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
