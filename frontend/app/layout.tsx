import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Krishiayan — farmer’s soil guide",
  description: "Raw probe readings to fertilizer what/when, crop condition, and weather.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
