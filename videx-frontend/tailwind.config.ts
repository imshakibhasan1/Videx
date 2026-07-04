import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      // ── Antigravity Color Palette ──────────────────────────────────
      colors: {
        videx: {
          // Core brand gradient anchors
          50: "#f0f0ff",
          100: "#e0e0ff",
          200: "#c4b5fd",
          300: "#a78bfa",
          400: "#8b5cf6",
          500: "#7c3aed", // Primary brand
          600: "#6d28d9",
          700: "#5b21b6",
          800: "#4c1d95",
          900: "#3b0764",
          950: "#1e0040",
        },
        surface: {
          DEFAULT: "rgba(15, 15, 25, 1)",
          raised: "rgba(22, 22, 38, 1)",
          overlay: "rgba(30, 30, 50, 0.85)",
          glass: "rgba(255, 255, 255, 0.03)",
          "glass-hover": "rgba(255, 255, 255, 0.06)",
          "glass-active": "rgba(255, 255, 255, 0.09)",
        },
        glow: {
          purple: "rgba(124, 58, 237, 0.4)",
          blue: "rgba(59, 130, 246, 0.4)",
          pink: "rgba(236, 72, 153, 0.3)",
          cyan: "rgba(6, 182, 212, 0.35)",
          success: "rgba(34, 197, 94, 0.3)",
        },
        border: {
          subtle: "rgba(255, 255, 255, 0.06)",
          medium: "rgba(255, 255, 255, 0.1)",
          bright: "rgba(255, 255, 255, 0.15)",
          glow: "rgba(124, 58, 237, 0.3)",
        },
      },

      // ── Antigravity Fonts ──────────────────────────────────────────
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["var(--font-jetbrains)", "Menlo", "monospace"],
        display: ["var(--font-outfit)", "var(--font-inter)", "sans-serif"],
      },

      // ── Antigravity Floating Shadows ───────────────────────────────
      boxShadow: {
        // Card shadows — layered for depth
        "float-sm": "0 4px 20px rgba(0, 0, 0, 0.3), 0 0 40px rgba(124, 58, 237, 0.05)",
        "float-md": "0 8px 40px rgba(0, 0, 0, 0.4), 0 0 60px rgba(124, 58, 237, 0.08)",
        "float-lg": "0 16px 60px rgba(0, 0, 0, 0.5), 0 0 80px rgba(124, 58, 237, 0.12)",
        "float-xl": "0 24px 80px rgba(0, 0, 0, 0.6), 0 0 120px rgba(124, 58, 237, 0.15)",

        // Glow shadows for active/selected states
        "glow-purple": "0 0 20px rgba(124, 58, 237, 0.4), 0 0 60px rgba(124, 58, 237, 0.15)",
        "glow-blue": "0 0 20px rgba(59, 130, 246, 0.4), 0 0 60px rgba(59, 130, 246, 0.15)",
        "glow-pink": "0 0 20px rgba(236, 72, 153, 0.4), 0 0 60px rgba(236, 72, 153, 0.15)",
        "glow-cyan": "0 0 20px rgba(6, 182, 212, 0.4), 0 0 60px rgba(6, 182, 212, 0.15)",
        "glow-success": "0 0 20px rgba(34, 197, 94, 0.4), 0 0 60px rgba(34, 197, 94, 0.12)",

        // Inner glow for input fields
        "inner-glow": "inset 0 0 20px rgba(124, 58, 237, 0.1)",
      },

      // ── Antigravity Keyframe Animations ────────────────────────────
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-8px)" },
        },
        "float-slow": {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-12px)" },
        },
        "float-subtle": {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-4px)" },
        },
        "glow-pulse": {
          "0%, 100%": { opacity: "0.4" },
          "50%": { opacity: "0.8" },
        },
        "shimmer": {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        "fade-in-up": {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "scale-in": {
          "0%": { opacity: "0", transform: "scale(0.9)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        "orbit": {
          "0%": { transform: "rotate(0deg) translateX(6px) rotate(0deg)" },
          "100%": { transform: "rotate(360deg) translateX(6px) rotate(-360deg)" },
        },
      },
      animation: {
        float: "float 4s ease-in-out infinite",
        "float-slow": "float-slow 6s ease-in-out infinite",
        "float-subtle": "float-subtle 3s ease-in-out infinite",
        "glow-pulse": "glow-pulse 3s ease-in-out infinite",
        shimmer: "shimmer 2s linear infinite",
        "fade-in-up": "fade-in-up 0.5s ease-out",
        "scale-in": "scale-in 0.3s ease-out",
        orbit: "orbit 8s linear infinite",
      },

      // ── Backdrop Blur extensions ───────────────────────────────────
      backdropBlur: {
        xs: "2px",
        "2xl": "40px",
        "3xl": "64px",
      },

      // ── Border Radius ──────────────────────────────────────────────
      borderRadius: {
        "4xl": "2rem",
        "5xl": "2.5rem",
      },

      // ── Transitions ────────────────────────────────────────────────
      transitionDuration: {
        "400": "400ms",
        "600": "600ms",
      },
      transitionTimingFunction: {
        "out-expo": "cubic-bezier(0.16, 1, 0.3, 1)",
        spring: "cubic-bezier(0.34, 1.56, 0.64, 1)",
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
};

export default config;
