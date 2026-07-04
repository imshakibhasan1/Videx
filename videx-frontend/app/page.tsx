/**
 * VIDEX Landing Page.
 *
 * For MVP, this renders the dashboard directly.
 * In future, this will be a marketing/landing page
 * with the dashboard moved to /dashboard.
 */

"use client";

import { motion } from "framer-motion";
import { Sparkles, ArrowRight, Zap, Shield, Clock } from "lucide-react";
import { FloatingCardAnimated } from "@/components/antigravity/FloatingCard";
import { ParticleField } from "@/components/antigravity/ParticleField";
import { Navbar } from "@/components/layout/Navbar";
import Link from "next/link";

const features = [
  {
    icon: Zap,
    title: "AI-Powered Analysis",
    description:
      "MiMo V2.5 deconstructs your video frame by frame — extracting lighting, camera physics, and motion dynamics.",
  },
  {
    icon: Shield,
    title: "Physics Compliant",
    description:
      "Every generated prompt respects real-world physics: gravity, optics, fluid dynamics, and temporal coherence.",
  },
  {
    icon: Clock,
    title: "Instant Prompts",
    description:
      "From upload to production-ready T2V prompt in under 60 seconds. Copy, paste, generate.",
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen relative">
      <ParticleField count={30} />
      <Navbar />

      <main className="relative z-10 pt-32 pb-20">
        <div className="section-container">
          {/* ── Hero ────────────────────────────────────────────────── */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
            className="text-center max-w-4xl mx-auto"
          >
            <div className="inline-flex items-center gap-2 rounded-full bg-videx-500/10 border border-videx-500/20 px-4 py-1.5 mb-6">
              <Sparkles className="h-4 w-4 text-videx-400" />
              <span className="text-sm font-medium text-videx-300">
                Powered by MiMo V2.5
              </span>
            </div>

            <h1 className="font-display text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight leading-[1.1] text-balance">
              <span className="gradient-text">Reverse-engineer</span>
              <br />
              <span className="text-white/90">any video into a prompt</span>
            </h1>

            <p className="mt-6 text-lg sm:text-xl text-white/50 max-w-2xl mx-auto leading-relaxed">
              Upload a clip, and our AI extracts ultra-realistic Text-to-Video
              prompts ready for Sora, Kling, Runway, and more.
            </p>

            <div className="mt-10 flex items-center justify-center gap-4">
              <Link href="/dashboard">
                <motion.div
                  whileHover={{ scale: 1.05, y: -2 }}
                  whileTap={{ scale: 0.96 }}
                  className="btn-glow text-base px-8 py-4"
                >
                  <Sparkles className="h-5 w-5" />
                  Start Analyzing
                  <ArrowRight className="h-5 w-5" />
                </motion.div>
              </Link>
            </div>
          </motion.div>

          {/* ── Features ──────────────────────────────────────────── */}
          <div className="mt-28 grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {features.map((feature, i) => (
              <FloatingCardAnimated
                key={feature.title}
                delay={0.15 * (i + 1)}
                amplitude={5}
              >
                <div className="p-6">
                  <div className="h-11 w-11 rounded-xl bg-videx-500/10 border border-videx-500/20 flex items-center justify-center mb-4">
                    <feature.icon className="h-5 w-5 text-videx-400" />
                  </div>
                  <h3 className="font-display text-base font-semibold text-white/90 mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-sm text-white/45 leading-relaxed">
                    {feature.description}
                  </p>
                </div>
              </FloatingCardAnimated>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
