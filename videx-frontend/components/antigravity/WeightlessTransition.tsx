/**
 * WeightlessTransition — Antigravity Layout Transition Wrapper.
 *
 * Wraps content sections that transition between pipeline steps.
 * When children change, the outgoing content fades + slides down (gravity pull)
 * and the incoming content fades + floats up (antigravity entrance).
 *
 * Uses AnimatePresence + motion.div with layout animations.
 */

"use client";

import { type ReactNode } from "react";
import { AnimatePresence, motion, type Variants } from "framer-motion";
import { cn } from "@/lib/utils";

interface WeightlessTransitionProps {
  /** Unique key to trigger re-mount and transition. */
  transitionKey: string;
  /** Content to render. */
  children: ReactNode;
  /** Transition mode: "wait" (default) or "popLayout" or "sync". */
  mode?: "wait" | "popLayout" | "sync";
  /** Animation duration in seconds. */
  duration?: number;
  /** Additional Tailwind classes. */
  className?: string;
}

const weightlessVariants: Variants = {
  // ── Entry: float up from below ─────────────────────────────────────
  initial: {
    opacity: 0,
    y: 30,
    scale: 0.97,
    filter: "blur(4px)",
  },
  // ── Visible: resting in zero-g ─────────────────────────────────────
  animate: {
    opacity: 1,
    y: 0,
    scale: 1,
    filter: "blur(0px)",
  },
  // ── Exit: pulled down by gravity ───────────────────────────────────
  exit: {
    opacity: 0,
    y: -20,
    scale: 0.98,
    filter: "blur(4px)",
  },
};

export function WeightlessTransition({
  transitionKey,
  children,
  mode = "wait",
  duration = 0.4,
  className,
}: WeightlessTransitionProps) {
  return (
    <AnimatePresence mode={mode}>
      <motion.div
        key={transitionKey}
        variants={weightlessVariants}
        initial="initial"
        animate="animate"
        exit="exit"
        transition={{
          duration,
          ease: [0.16, 1, 0.3, 1], // out-expo
        }}
        className={cn("w-full", className)}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}

/**
 * StaggerContainer — Animates children with sequential delays.
 *
 * Wrap a list of items to get cascading float-up entrance.
 */
interface StaggerContainerProps {
  children: ReactNode;
  /** Delay between each child in seconds. */
  stagger?: number;
  /** Initial delay before the first child animates. */
  delay?: number;
  className?: string;
}

const staggerContainerVariants: Variants = {
  hidden: {},
  visible: (stagger: number) => ({
    transition: {
      staggerChildren: stagger,
    },
  }),
};

const staggerItemVariants: Variants = {
  hidden: {
    opacity: 0,
    y: 24,
    scale: 0.95,
  },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      duration: 0.5,
      ease: [0.16, 1, 0.3, 1],
    },
  },
};

export function StaggerContainer({
  children,
  stagger = 0.08,
  delay = 0,
  className,
}: StaggerContainerProps) {
  return (
    <motion.div
      variants={staggerContainerVariants}
      initial="hidden"
      animate="visible"
      custom={stagger}
      transition={{ delayChildren: delay }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

export function StaggerItem({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <motion.div variants={staggerItemVariants} className={className}>
      {children}
    </motion.div>
  );
}
