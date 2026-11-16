import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Martian Route",
  description: "Layered map and walk planner for the first explorers of Mars",
  openGraph: {
    title: "Martian Route",
    description: "Plan a walk on Mars and compare routes by slope, obstacles, oxygen and safe return.",
    type: "website",
  },
};

// Browser bar color on phones: the same background as the page.
export const viewport: Viewport = {
  themeColor: "#0b0605",
  colorScheme: "dark",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
