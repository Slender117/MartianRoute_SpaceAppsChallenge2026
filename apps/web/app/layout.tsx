import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Martian Route",
  description: "Mapa por capas y planificador de caminatas para los primeros exploradores de Marte",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
