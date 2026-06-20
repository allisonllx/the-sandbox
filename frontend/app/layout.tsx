import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "The Sandbox — CTO Dashboard",
  description: "Zero-trust R&D talent platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-surface text-slate-200">{children}</body>
    </html>
  );
}
