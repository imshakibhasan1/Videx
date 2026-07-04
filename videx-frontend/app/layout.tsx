/**
 * VIDEX Root Layout.
 *
 * - Loads Google Fonts (Inter, Outfit, JetBrains Mono)
 * - Wraps the app in providers (Motion, Toast)
 * - Sets meta tags and dark theme
 */

import type { Metadata, Viewport } from "next";
import { Inter, Outfit, JetBrains_Mono } from "next/font/google";
import { MotionProvider } from "@/components/providers/MotionProvider";
import { ToastProvider } from "@/components/providers/ToastProvider";
import "./globals.css";

// ── Font Loading ────────────────────────────────────────────────────────────

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
  display: "swap",
});

const jetbrains = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains",
  display: "swap",
});

// ── Metadata ────────────────────────────────────────────────────────────────

export const metadata: Metadata = {
  title: {
    default: "VIDEX — AI Video Reverse-Engineering",
    template: "%s | VIDEX",
  },
  description:
    "Upload any video and get physics-compliant, ultra-realistic Text-to-Video prompts powered by MiMo V2.5 AI.",
  keywords: [
    "AI",
    "video analysis",
    "text-to-video",
    "prompt engineering",
    "Sora",
    "Kling",
    "MiMo",
    "reverse engineering",
  ],
  authors: [{ name: "VIDEX", url: "https://videx.app" }],
  openGraph: {
    title: "VIDEX — AI Video Reverse-Engineering Platform",
    description:
      "Transform any video into production-quality Text-to-Video prompts.",
    siteName: "VIDEX",
    type: "website",
  },
};

export const viewport: Viewport = {
  themeColor: "#0f0f19",
  colorScheme: "dark",
};

// ── Layout ──────────────────────────────────────────────────────────────────

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${outfit.variable} ${jetbrains.variable} dark`}
      suppressHydrationWarning
    >
      <body className="font-sans bg-surface text-white min-h-screen">
        <MotionProvider>
          {children}
          <ToastProvider />
        </MotionProvider>
      </body>
    </html>
  );
}
