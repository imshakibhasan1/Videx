/**
 * Login Page — Email/password authentication.
 */

"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Sparkles, Mail, Lock, User, ArrowRight, Eye, EyeOff } from "lucide-react";
import { FloatingCardAnimated } from "@/components/antigravity/FloatingCard";
import { ParticleField } from "@/components/antigravity/ParticleField";
import { Navbar } from "@/components/layout/Navbar";
import { login, register } from "@/lib/api";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import type { ApiError } from "@/types/api.types";

type Mode = "login" | "register";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("login");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", password: "" });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const result = mode === "login"
        ? await login({ email: form.email, password: form.password })
        : await register({ name: form.name, email: form.email, password: form.password });

      // Store tokens
      localStorage.setItem("videx_access_token", result.access_token);
      localStorage.setItem("videx_refresh_token", result.refresh_token);

      toast.success(mode === "login" ? "Welcome back!" : "Account created!");
      router.push("/dashboard");
    } catch (err) {
      const apiErr = err as ApiError;
      toast.error(apiErr?.message || "Authentication failed.");
    } finally {
      setIsLoading(false);
    }
  };

  const inputClass = cn(
    "w-full rounded-xl border border-border-subtle bg-surface-glass",
    "px-4 py-3 pl-11 text-sm text-white placeholder:text-white/30",
    "backdrop-blur-sm transition-all duration-300",
    "focus:outline-none focus:border-videx-500/40 focus:shadow-inner-glow focus:ring-1 focus:ring-videx-500/20"
  );

  return (
    <div className="min-h-screen relative flex items-center justify-center">
      <ParticleField count={25} />
      <Navbar />

      <main className="relative z-10 w-full max-w-md px-4 pt-20">
        <FloatingCardAnimated delay={0.1} amplitude={4}>
          <div className="p-8">
            {/* Header */}
            <div className="text-center mb-8">
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: "spring", stiffness: 300, damping: 20, delay: 0.2 }}
                className="inline-flex items-center justify-center h-14 w-14 rounded-2xl bg-videx-500/10 border border-videx-500/20 mb-4"
              >
                <Sparkles className="h-7 w-7 text-videx-400" />
              </motion.div>
              <h1 className="font-display text-2xl font-bold text-white/90">
                {mode === "login" ? "Welcome back" : "Create your account"}
              </h1>
              <p className="mt-1 text-sm text-white/40">
                {mode === "login" ? "Sign in to continue" : "Start reverse-engineering videos"}
              </p>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              {mode === "register" && (
                <div className="relative">
                  <User className="absolute left-3.5 top-3.5 h-4 w-4 text-white/30" />
                  <input
                    type="text"
                    placeholder="Full name"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    className={inputClass}
                    required
                    minLength={2}
                  />
                </div>
              )}

              <div className="relative">
                <Mail className="absolute left-3.5 top-3.5 h-4 w-4 text-white/30" />
                <input
                  type="email"
                  placeholder="Email address"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  className={inputClass}
                  required
                />
              </div>

              <div className="relative">
                <Lock className="absolute left-3.5 top-3.5 h-4 w-4 text-white/30" />
                <input
                  type={showPassword ? "text" : "password"}
                  placeholder="Password"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  className={cn(inputClass, "pr-11")}
                  required
                  minLength={8}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-3.5 text-white/30 hover:text-white/60 transition-colors"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>

              <motion.button
                type="submit"
                disabled={isLoading}
                whileHover={!isLoading ? { scale: 1.02 } : {}}
                whileTap={!isLoading ? { scale: 0.98 } : {}}
                className="btn-glow w-full py-3.5 text-sm mt-2"
              >
                {isLoading ? (
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                    className="h-4 w-4 rounded-full border-2 border-white/30 border-t-white"
                  />
                ) : (
                  <>
                    {mode === "login" ? "Sign In" : "Create Account"}
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </motion.button>
            </form>

            {/* Toggle mode */}
            <div className="mt-6 text-center">
              <button
                onClick={() => setMode(mode === "login" ? "register" : "login")}
                className="text-sm text-white/40 hover:text-white/70 transition-colors"
              >
                {mode === "login" ? (
                  <>Don&apos;t have an account? <span className="text-videx-400">Sign up</span></>
                ) : (
                  <>Already have an account? <span className="text-videx-400">Sign in</span></>
                )}
              </button>
            </div>
          </div>
        </FloatingCardAnimated>
      </main>
    </div>
  );
}
