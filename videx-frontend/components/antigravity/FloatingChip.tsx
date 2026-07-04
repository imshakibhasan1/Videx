/**
 * FloatingChip — Antigravity Selection Pill.
 *
 * An interactive chip/pill that hovers upward on hover,
 * glows with a box-shadow when active, and springs with
 * satisfying tactile feedback on click.
 *
 * Used for: Duration (8s/10s/15s), Aspect Ratio, Style selection.
 */

"use client";

import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

interface FloatingChipProps {
  /** Display label (e.g. "8s", "16:9", "Original Style"). */
  label: string;
  /** Whether this chip is currently selected. */
  selected?: boolean;
  /** Optional emoji or icon to prefix. */
  icon?: string;
  /** Click handler to toggle selection. */
  onClick: () => void;
  /** Glow color variant when active. */
  glowColor?: "purple" | "blue" | "pink" | "cyan" | "success";
  /** Stagger delay for entry animation. */
  delay?: number;
  /** Disabled state. */
  disabled?: boolean;
  /** Additional Tailwind classes. */
  className?: string;
}

const glowMap = {
  purple: {
    shadow: "0 0 20px rgba(124, 58, 237, 0.5), 0 0 60px rgba(124, 58, 237, 0.15)",
    bg: "rgba(124, 58, 237, 0.2)",
    border: "rgba(124, 58, 237, 0.4)",
    ring: "ring-videx-500/30",
  },
  blue: {
    shadow: "0 0 20px rgba(59, 130, 246, 0.5), 0 0 60px rgba(59, 130, 246, 0.15)",
    bg: "rgba(59, 130, 246, 0.2)",
    border: "rgba(59, 130, 246, 0.4)",
    ring: "ring-blue-500/30",
  },
  pink: {
    shadow: "0 0 20px rgba(236, 72, 153, 0.5), 0 0 60px rgba(236, 72, 153, 0.15)",
    bg: "rgba(236, 72, 153, 0.2)",
    border: "rgba(236, 72, 153, 0.4)",
    ring: "ring-pink-500/30",
  },
  cyan: {
    shadow: "0 0 20px rgba(6, 182, 212, 0.5), 0 0 60px rgba(6, 182, 212, 0.15)",
    bg: "rgba(6, 182, 212, 0.2)",
    border: "rgba(6, 182, 212, 0.4)",
    ring: "ring-cyan-500/30",
  },
  success: {
    shadow: "0 0 20px rgba(34, 197, 94, 0.5), 0 0 60px rgba(34, 197, 94, 0.12)",
    bg: "rgba(34, 197, 94, 0.2)",
    border: "rgba(34, 197, 94, 0.4)",
    ring: "ring-green-500/30",
  },
};

export function FloatingChip({
  label,
  selected = false,
  icon,
  onClick,
  glowColor = "purple",
  delay = 0,
  disabled = false,
  className,
}: FloatingChipProps) {
  const glow = glowMap[glowColor];

  return (
    <motion.button
      type="button"
      onClick={onClick}
      disabled={disabled}
      // ── Entry animation ────────────────────────────────────────────
      initial={{ opacity: 0, y: 16, scale: 0.9 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{
        duration: 0.4,
        delay,
        ease: [0.16, 1, 0.3, 1],
      }}
      // ── Hover: float upward + subtle scale ─────────────────────────
      whileHover={
        disabled
          ? {}
          : {
              y: -4,
              scale: 1.06,
              transition: { duration: 0.2, ease: [0.34, 1.56, 0.64, 1] },
            }
      }
      // ── Tap: satisfying spring compression ─────────────────────────
      whileTap={
        disabled
          ? {}
          : {
              scale: 0.94,
              transition: { duration: 0.1 },
            }
      }
      // ── Selection glow (animated via Framer Motion) ────────────────
      style={{
        boxShadow: selected ? glow.shadow : "0 0 0px rgba(0,0,0,0)",
        backgroundColor: selected ? glow.bg : "rgba(255, 255, 255, 0.04)",
        borderColor: selected ? glow.border : "rgba(255, 255, 255, 0.08)",
      }}
      className={cn(
        // Base
        "relative inline-flex items-center gap-2",
        "rounded-full px-5 py-2.5",
        "border text-sm font-medium",
        "backdrop-blur-sm select-none",
        "transition-colors duration-200",
        // Text color
        selected ? "text-white" : "text-white/60",
        // Hover text
        !selected && !disabled && "hover:text-white",
        // Disabled
        disabled && "opacity-40 cursor-not-allowed",
        !disabled && "cursor-pointer",
        className
      )}
    >
      {/* Icon */}
      {icon && <span className="text-base">{icon}</span>}

      {/* Label */}
      <span className="relative z-10">{label}</span>

      {/* Active indicator dot */}
      <AnimatePresence>
        {selected && (
          <motion.span
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: [0.34, 1.56, 0.64, 1] }}
            className="absolute -top-1 -right-1 h-2.5 w-2.5 rounded-full bg-white/80"
            style={{
              boxShadow: glow.shadow,
            }}
          />
        )}
      </AnimatePresence>
    </motion.button>
  );
}
