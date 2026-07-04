/**
 * FloatingCard — Antigravity Physics Card Component.
 *
 * A glassmorphic card that continuously oscillates on the y-axis,
 * creating a "floating in zero-gravity" effect. On hover, it lifts
 * higher and scales slightly, as if touched by a magnetic field.
 *
 * Uses Framer Motion for GPU-accelerated animations.
 */

"use client";

import { type ReactNode } from "react";
import { motion, type Variants } from "framer-motion";
import { cn } from "@/lib/utils";

interface FloatingCardProps {
  children: ReactNode;
  /** Stagger delay in seconds before float animation starts. */
  delay?: number;
  /** Float amplitude in pixels (default: 8). */
  amplitude?: number;
  /** Float cycle duration in seconds (default: 4). */
  duration?: number;
  /** Disable the continuous float (useful during interaction). */
  disableFloat?: boolean;
  /** Additional Tailwind classes. */
  className?: string;
  /** Click handler. */
  onClick?: () => void;
}

const cardVariants: Variants = {
  hidden: {
    opacity: 0,
    y: 40,
    scale: 0.95,
  },
  visible: (delay: number) => ({
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      opacity: { duration: 0.5, delay, ease: "easeOut" },
      y: { duration: 0.6, delay, ease: [0.16, 1, 0.3, 1] },
      scale: { duration: 0.5, delay, ease: "easeOut" },
    },
  }),
};

export function FloatingCard({
  children,
  delay = 0,
  amplitude = 8,
  duration = 4,
  disableFloat = false,
  className,
  onClick,
}: FloatingCardProps) {
  return (
    <motion.div
      // ── Entry animation ────────────────────────────────────────────
      variants={cardVariants}
      initial="hidden"
      animate="visible"
      custom={delay}
      // ── Hover magnetic lift ────────────────────────────────────────
      whileHover={{
        y: disableFloat ? -8 : undefined,
        scale: 1.02,
        transition: { duration: 0.25, ease: [0.34, 1.56, 0.64, 1] },
      }}
      whileTap={onClick ? { scale: 0.98 } : undefined}
      onClick={onClick}
      className={cn(
        // Glass card base
        "relative overflow-hidden rounded-2xl",
        "border border-border-subtle",
        "bg-surface-glass backdrop-blur-xl",
        "shadow-float-md",
        // Cursor
        onClick && "cursor-pointer",
        className
      )}
    >
      {/* Gradient shimmer overlay */}
      <div
        className="pointer-events-none absolute inset-0 rounded-2xl"
        style={{
          background:
            "linear-gradient(135deg, rgba(255,255,255,0.04) 0%, transparent 60%)",
        }}
      />

      {/* Content */}
      <div className="relative z-10">{children}</div>

      {/* Continuous float animation — separate motion div to isolate transforms */}
      {!disableFloat && (
        <motion.div
          className="absolute inset-0 pointer-events-none"
          animate={{
            y: [0, -amplitude, 0],
          }}
          transition={{
            y: {
              duration,
              repeat: Infinity,
              ease: "easeInOut",
              delay: delay + 0.6,
            },
          }}
          style={{
            // Apply the float to the parent via CSS containment trick
            // This is handled by the parent wrapper below
          }}
        />
      )}
    </motion.div>
  );
}

/**
 * FloatingCardBody — Wraps card content and applies the y-axis oscillation
 * to the entire card via a motion wrapper. Use this instead of FloatingCard
 * when you need the float to affect the card position, not just an inner layer.
 */
export function FloatingCardAnimated({
  children,
  delay = 0,
  amplitude = 8,
  duration = 4,
  disableFloat = false,
  className,
  onClick,
}: FloatingCardProps) {
  return (
    <motion.div
      // ── Entry ──────────────────────────────────────────────────────
      initial={{ opacity: 0, y: 40, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{
        opacity: { duration: 0.5, delay },
        y: { duration: 0.6, delay, ease: [0.16, 1, 0.3, 1] },
        scale: { duration: 0.5, delay },
      }}
      className="will-change-transform"
    >
      <motion.div
        // ── Continuous y-axis float ──────────────────────────────────
        animate={
          disableFloat
            ? {}
            : {
                y: [0, -amplitude, 0],
              }
        }
        transition={{
          y: {
            duration,
            repeat: Infinity,
            ease: "easeInOut",
            delay: delay + 0.6,
          },
        }}
        // ── Hover ────────────────────────────────────────────────────
        whileHover={{
          y: -amplitude * 2,
          scale: 1.02,
          transition: { duration: 0.25, ease: [0.34, 1.56, 0.64, 1] },
        }}
        whileTap={onClick ? { scale: 0.98 } : undefined}
        onClick={onClick}
        className={cn(
          "relative overflow-hidden rounded-2xl",
          "border border-border-subtle",
          "bg-surface-glass backdrop-blur-xl",
          "shadow-float-md",
          "transition-shadow duration-400 ease-out-expo",
          "hover:shadow-float-lg hover:border-border-bright",
          onClick && "cursor-pointer",
          className
        )}
      >
        {/* Shimmer overlay */}
        <div
          className="pointer-events-none absolute inset-0 rounded-2xl"
          style={{
            background:
              "linear-gradient(135deg, rgba(255,255,255,0.04) 0%, transparent 60%)",
          }}
        />
        <div className="relative z-10">{children}</div>
      </motion.div>
    </motion.div>
  );
}
