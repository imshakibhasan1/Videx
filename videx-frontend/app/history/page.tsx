/**
 * History Page — Displays the user's past generated prompts.
 */

"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { History, Copy, ExternalLink, Sparkles } from "lucide-react";
import { FloatingCardAnimated } from "@/components/antigravity/FloatingCard";
import { StaggerContainer, StaggerItem } from "@/components/antigravity/WeightlessTransition";
import { ParticleField } from "@/components/antigravity/ParticleField";
import { Navbar } from "@/components/layout/Navbar";
import { listPrompts, trackCopy } from "@/lib/api";
import { cn, scoreColor, copyToClipboard, truncate } from "@/lib/utils";
import type { GeneratedPrompt } from "@/types/api.types";
import { toast } from "sonner";

export default function HistoryPage() {
  const [prompts, setPrompts] = useState<GeneratedPrompt[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    async function load() {
      setIsLoading(true);
      try {
        const res = await listPrompts(page, 12);
        setPrompts(res.items);
        setTotal(res.total);
      } catch {
        toast.error("Failed to load prompt history.");
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, [page]);

  const handleCopy = async (prompt: GeneratedPrompt) => {
    const ok = await copyToClipboard(prompt.final_prompt);
    if (ok) {
      toast.success("Prompt copied!");
      trackCopy(prompt.prompt_id).catch(() => {});
    }
  };

  return (
    <div className="min-h-screen relative">
      <ParticleField count={20} />
      <Navbar />

      <main className="relative z-10 pt-24 pb-16">
        <div className="section-container">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="mb-10"
          >
            <div className="flex items-center gap-3">
              <History className="h-6 w-6 text-videx-400" />
              <h1 className="font-display text-3xl font-bold text-white/90">Prompt History</h1>
            </div>
            <p className="mt-2 text-sm text-white/40">
              {total} prompt{total !== 1 ? "s" : ""} generated
            </p>
          </motion.div>

          {/* Loading */}
          {isLoading && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="shimmer h-48 rounded-2xl" />
              ))}
            </div>
          )}

          {/* Empty state */}
          {!isLoading && prompts.length === 0 && (
            <div className="text-center py-20">
              <Sparkles className="h-12 w-12 text-white/10 mx-auto mb-4" />
              <p className="text-lg text-white/30">No prompts yet</p>
              <p className="text-sm text-white/20 mt-1">Upload a video to get started</p>
            </div>
          )}

          {/* Prompt Grid */}
          {!isLoading && prompts.length > 0 && (
            <StaggerContainer stagger={0.06} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {prompts.map((prompt) => (
                <StaggerItem key={prompt.prompt_id}>
                  <FloatingCardAnimated amplitude={3} delay={0} disableFloat>
                    <div className="p-5">
                      {/* Scores */}
                      <div className="flex items-center gap-2 mb-3">
                        <span className={cn("text-xs font-mono", scoreColor(prompt.physics_score))}>
                          P:{(prompt.physics_score * 100).toFixed(0)}%
                        </span>
                        <span className={cn("text-xs font-mono", scoreColor(prompt.quality_score))}>
                          Q:{(prompt.quality_score * 100).toFixed(0)}%
                        </span>
                        <span className="ml-auto text-[10px] text-white/20">
                          {new Date(prompt.created_at).toLocaleDateString()}
                        </span>
                      </div>

                      {/* Truncated prompt */}
                      <p className="text-xs text-white/50 leading-relaxed font-mono line-clamp-4">
                        {truncate(prompt.final_prompt, 200)}
                      </p>

                      {/* Metadata chips */}
                      <div className="flex flex-wrap gap-1.5 mt-3">
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 text-white/30">
                          {prompt.prompt_metadata.selected_style}
                        </span>
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 text-white/30">
                          {prompt.prompt_metadata.duration}
                        </span>
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 text-white/30">
                          {prompt.prompt_metadata.aspect_ratio}
                        </span>
                      </div>

                      {/* Actions */}
                      <div className="flex items-center gap-2 mt-4 pt-3 border-t border-border-subtle">
                        <button onClick={() => handleCopy(prompt)} className="btn-ghost text-xs py-1.5 px-3">
                          <Copy className="h-3 w-3" /> Copy
                        </button>
                        {prompt.is_public && prompt.share_token && (
                          <a href={`/share/${prompt.share_token}`} className="btn-ghost text-xs py-1.5 px-3">
                            <ExternalLink className="h-3 w-3" /> View
                          </a>
                        )}
                      </div>
                    </div>
                  </FloatingCardAnimated>
                </StaggerItem>
              ))}
            </StaggerContainer>
          )}

          {/* Pagination */}
          {total > 12 && (
            <div className="flex items-center justify-center gap-3 mt-10">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
                className="btn-ghost text-sm disabled:opacity-30"
              >
                Previous
              </button>
              <span className="text-sm text-white/30">
                Page {page} of {Math.ceil(total / 12)}
              </span>
              <button
                onClick={() => setPage(page + 1)}
                disabled={page >= Math.ceil(total / 12)}
                className="btn-ghost text-sm disabled:opacity-30"
              >
                Next
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
