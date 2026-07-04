/**
 * VIDEX Navbar — Global navigation bar.
 *
 * Features:
 * - Glassmorphic floating bar
 * - Gradient brand logo
 * - Auth-aware: shows Sign Out when a token is present, Sign In otherwise
 */

"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Sparkles, LogIn, LogOut, Clock } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";

interface NavbarProps {
  className?: string;
}

export function Navbar({ className }: NavbarProps) {
  const router = useRouter();
  const [isAuthed, setIsAuthed] = useState(false);

  // Read auth state from localStorage on mount (client only)
  useEffect(() => {
    const token = localStorage.getItem("videx_access_token");
    setIsAuthed(!!token);
  }, []);

  const handleSignOut = () => {
    localStorage.removeItem("videx_access_token");
    localStorage.removeItem("videx_refresh_token");
    setIsAuthed(false);
    router.push("/login");
  };

  return (
    <motion.header
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className={cn(
        "fixed top-0 left-0 right-0 z-50",
        "border-b border-border-subtle",
        "bg-surface/60 backdrop-blur-2xl",
        className
      )}
    >
      <div className="section-container flex h-16 items-center justify-between">
        {/* ── Logo ─────────────────────────────────────────────────────── */}
        <Link href={isAuthed ? "/dashboard" : "/"} className="flex items-center gap-2.5 group">
          <motion.div
            whileHover={{ rotate: 15, scale: 1.1 }}
            transition={{ type: "spring", stiffness: 300, damping: 15 }}
          >
            <Sparkles className="h-6 w-6 text-videx-400" />
          </motion.div>
          <span className="font-display text-xl font-bold tracking-tight gradient-text">
            VIDEX
          </span>
          <span className="hidden sm:inline-flex items-center gap-1 rounded-full bg-videx-500/10 border border-videx-500/20 px-2 py-0.5 text-[10px] font-medium text-videx-300 uppercase tracking-wider">
            Beta
          </span>
        </Link>

        {/* ── Navigation ───────────────────────────────────────────────── */}
        <nav className="flex items-center gap-3">
          {isAuthed ? (
            <>
              <Link href="/history" className="btn-ghost text-sm">
                <Clock className="h-4 w-4" />
                History
              </Link>
              <button onClick={handleSignOut} className="btn-ghost text-sm">
                <LogOut className="h-4 w-4" />
                <span>Sign Out</span>
              </button>
            </>
          ) : (
            <>
              <Link href="/history" className="btn-ghost text-sm">
                History
              </Link>
              <Link href="/login" className="btn-glow text-sm">
                <LogIn className="h-4 w-4" />
                <span>Sign In</span>
              </Link>
            </>
          )}
        </nav>
      </div>
    </motion.header>
  );
}
