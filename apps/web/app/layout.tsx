import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Martian Route",
  description: "Mapa por capas y planificador de caminatas para los primeros exploradores de Marte",
  openGraph: {
    title: "Martian Route",
    description: "Planea una caminata en Marte y compara rutas por pendiente, obstáculos, oxígeno y regreso seguro.",
    type: "website",
  },
};

// Color de la barra del navegador en el celular: el mismo fondo de la página.
export const viewport: Viewport = {
  themeColor: "#0b0605",
  colorScheme: "dark",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
