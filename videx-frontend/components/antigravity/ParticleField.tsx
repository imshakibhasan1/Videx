/**
 * ParticleField — Subtle background ambient particle system.
 *
 * Renders a field of tiny floating dots that drift slowly,
 * creating depth and a sense of weightless space behind content.
 * Uses CSS animations exclusively — no JS frame loops.
 *
 * Particles are generated client-side only to avoid SSR hydration
 * mismatches caused by Math.random() producing different values on
 * server vs client.
 */

"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface ParticleFieldProps {
  /** Number of particles (default: 40). */
  count?: number;
  className?: string;
}

interface Particle {
  id: number;
  x: number;    // % from left
  y: number;    // % from top
  size: number;  // px
  opacity: number;
  duration: number;  // float cycle seconds
  delay: number;
}

export function ParticleField({ count = 40, className }: ParticleFieldProps) {
  // Start with empty array — populated on client only to avoid hydration mismatch
  const [particles, setParticles] = useState<Particle[]>([]);

  useEffect(() => {
    setParticles(
      Array.from({ length: count }, (_, i) => ({
        id: i,
        x: Math.random() * 100,
        y: Math.random() * 100,
        size: Math.random() * 2 + 1,
        opacity: Math.random() * 0.3 + 0.05,
        duration: Math.random() * 6 + 4,
        delay: Math.random() * 4,
      }))
    );
  }, [count]);

  return (
    <div
      className={cn(
        "pointer-events-none fixed inset-0 overflow-hidden z-0",
        className
      )}
      aria-hidden
    >
      {particles.map((p) => (
        <motion.div
          key={p.id}
          className="absolute rounded-full bg-white"
          style={{
            left: `${p.x}%`,
            top: `${p.y}%`,
            width: p.size,
            height: p.size,
            opacity: p.opacity,
          }}
          animate={{
            y: [0, -p.size * 8, 0],
            x: [0, Math.sin(p.id) * 6, 0],
            opacity: [p.opacity, p.opacity * 1.8, p.opacity],
          }}
          transition={{
            duration: p.duration,
            repeat: Infinity,
            ease: "easeInOut",
            delay: p.delay,
          }}
        />
      ))}
    </div>
  );
}
