/**
 * MotionProvider — Framer Motion LazyMotion wrapper.
 *
 * Provides the Framer Motion feature set to all children via
 * lazy-loaded features for tree-shaking. Also disables
 * reduced-motion if user hasn't requested it.
 */

"use client";

import { type ReactNode } from "react";
import { LazyMotion, domAnimation } from "framer-motion";

export function MotionProvider({ children }: { children: ReactNode }) {
  return (
    <LazyMotion features={domAnimation}>
      {children}
    </LazyMotion>
  );
}
