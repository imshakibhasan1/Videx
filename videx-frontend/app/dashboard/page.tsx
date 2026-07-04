/**
 * VIDEX Dashboard Page — Main Upload & Pipeline View.
 *
 * The core application interface. Users:
 * 1. Upload a video (DropZone)
 * 2. View analysis results (Scene summary + Style options)
 * 3. Customize parameters (Duration, Ratio, Style chips)
 * 4. Generate and view the final T2V prompt
 *
 * Uses WeightlessTransition for smooth step-to-step transitions
 * and useSSE for real-time pipeline status from FastAPI.
 */

"use client";

import { motion } from "framer-motion";
import { Sparkles, ArrowRight, RotateCcw, Zap, AlertCircle, Copy, Download, Share2 } from "lucide-react";
import { FloatingCardAnimated } from "@/components/antigravity/FloatingCard";
import { FloatingChip } from "@/components/antigravity/FloatingChip";
import { WeightlessTransition } from "@/components/antigravity/WeightlessTransition";
import { ParticleField } from "@/components/antigravity/ParticleField";
import { Navbar } from "@/components/layout/Navbar";
import { DropZone } from "@/components/upload/DropZone";
import { useSSE } from "@/hooks/useSSE";
import { useVidexStore } from "@/store/videx.store";
import {
  DURATION_OPTIONS,
  ASPECT_RATIO_OPTIONS,
  FRAME_RATE_OPTIONS,
  STYLE_CONFIG,
} from "@/lib/constants";
import { cn, scoreColor, copyToClipboard } from "@/lib/utils";
import { generatePrompt } from "@/lib/api";
import { toast } from "sonner";

export default function DashboardPage() {
  const {
    step,
    errorMessage,
    upload,
    analysis,
    customization,
    generatedPrompt,
    setSelectedStyle,
    setDuration,
    setAspectRatio,
    setFrameRate,
    setGenerating,
    setError,
    resetPipeline,
  } = useVidexStore();

  // SSE: auto-connect when we have a jobId and pipeline is active
  const shouldConnect = ["analyzing", "generating"].includes(step);
  useSSE({ jobId: shouldConnect ? upload.jobId : null });

  // ── Trigger Step 3 ─────────────────────────────────────────────────────────
  const handleGenerate = async () => {
    if (!upload.jobId || !analysis) return;
    setGenerating();
    try {
      await generatePrompt({
        job_id: upload.jobId,
        analysis_id: analysis.analysis_id,
        selected_style: customization.selectedStyle,
        duration: customization.duration,
        aspect_ratio: customization.aspectRatio,
        frame_rate: customization.frameRate,
      });
    } catch (err: any) {
      setError(err?.message || "Failed to start prompt generation.");
    }
  };

  // ── Copy prompt text ───────────────────────────────────────────────────────
  const handleCopy = async () => {
    if (!generatedPrompt) return;
    const ok = await copyToClipboard(generatedPrompt.final_prompt);
    ok ? toast.success("Prompt copied to clipboard!") : toast.error("Failed to copy.");
  };

  // ── Download as JSON ───────────────────────────────────────────────────────
  const handleDownload = () => {
    if (!generatedPrompt) return;
    const blob = new Blob([JSON.stringify(generatedPrompt, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `videx-prompt-${generatedPrompt.prompt_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success("Prompt JSON downloaded.");
  };

  return (
    <div className="min-h-screen relative">
      <ParticleField count={35} />
      <Navbar />

      <main className="relative z-10 pt-24 pb-16">
        <div className="section-container">
          {/* ── Hero Header ──────────────────────────────────────────── */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
            className="text-center mb-12"
          >
            <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-balance">
              <span className="gradient-text">Reverse-engineer</span>{" "}
              <span className="text-white/90">any video</span>
            </h1>
            <p className="mt-4 text-lg text-white/50 max-w-2xl mx-auto">
              Upload a clip, and our AI extracts physics-compliant Text-to-Video
              prompts you can drop straight into Sora, Kling, or Wan.
            </p>
          </motion.div>

          {/* ── Pipeline Steps ────────────────────────────────────────── */}
          <WeightlessTransition transitionKey={step}>

            {/* ═══ IDLE / UPLOADING ════════════════════════════════════ */}
            {(step === "idle" || step === "uploading" || step === "upload_done") && (
              <DropZone />
            )}

            {/* ═══ ANALYZING ═══════════════════════════════════════════ */}
            {step === "analyzing" && (
              <div className="flex flex-col items-center gap-6 py-16">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                  className="h-12 w-12 rounded-full border-2 border-videx-500/30 border-t-videx-400"
                />
                <div className="text-center">
                  <p className="text-lg font-medium text-white/80">
                    Analyzing your video with MiMo V2.5…
                  </p>
                  <p className="mt-1 text-sm text-white/40">
                    Extracting scene physics, lighting, and camera properties
                  </p>
                </div>
              </div>
            )}

            {/* ═══ ANALYSIS DONE + CUSTOMIZING ═════════════════════════ */}
            {(step === "analysis_done" || step === "customizing") && analysis && (
              <div className="max-w-4xl mx-auto space-y-10">

                {/* Scene Summary */}
                <FloatingCardAnimated delay={0} amplitude={6}>
                  <div className="p-6">
                    <div className="flex items-center gap-2 mb-3">
                      <Zap className="h-5 w-5 text-videx-400" />
                      <h2 className="font-display text-lg font-semibold text-white/90">
                        Scene Analysis
                      </h2>
                      <span className={cn(
                        "ml-auto text-sm font-mono px-2.5 py-0.5 rounded-full",
                        "bg-surface-glass border border-border-subtle",
                        scoreColor(analysis.confidence_score)
                      )}>
                        {(analysis.confidence_score * 100).toFixed(0)}% confidence
                      </span>
                    </div>
                    <p className="text-white/60 text-sm leading-relaxed">
                      {analysis.scene_summary}
                    </p>

                    {/* Physics Flags */}
                    <div className="mt-4 grid grid-cols-2 gap-3">
                      {Object.entries(analysis.physics_flags).map(([key, val]) => (
                        <div key={key} className="text-xs text-white/40">
                          <span className="text-white/25 uppercase tracking-wider text-[10px]">
                            {key.replace(/_/g, " ")}
                          </span>
                          <p className="mt-0.5 text-white/50">{val}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </FloatingCardAnimated>

                {/* Style Options */}
                <div>
                  <h3 className="font-display text-base font-semibold text-white/70 mb-4 text-center">
                    Choose a Visual Style
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    {analysis.style_options.map((style, i) => {
                      const cfg = STYLE_CONFIG[style.id as keyof typeof STYLE_CONFIG];
                      const selected = customization.selectedStyle === style.id;
                      return (
                        <FloatingCardAnimated
                          key={style.id}
                          delay={0.1 * (i + 1)}
                          amplitude={5}
                          onClick={() => setSelectedStyle(style.id as any)}
                          className={cn(selected && [cfg.borderActive, cfg.glowClass])}
                        >
                          <div className={cn("p-5 bg-gradient-to-br", cfg.gradient)}>
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-xl">{cfg.icon}</span>
                              <h4 className="font-semibold text-white/90">{style.label}</h4>
                            </div>
                            <p className="text-xs text-white/50 leading-relaxed">{style.description}</p>
                            <div className="flex flex-wrap gap-1.5 mt-3">
                              {style.mood_tags.map((tag) => (
                                <span key={tag} className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 text-white/40">
                                  {tag}
                                </span>
                              ))}
                            </div>
                          </div>
                        </FloatingCardAnimated>
                      );
                    })}
                  </div>
                </div>

                {/* Duration */}
                <div className="text-center">
                  <h3 className="font-display text-base font-semibold text-white/70 mb-4">Duration</h3>
                  <div className="flex items-center justify-center gap-3 flex-wrap">
                    {DURATION_OPTIONS.map((d, i) => (
                      <FloatingChip key={d} label={d} icon="⏱" selected={customization.duration === d} onClick={() => setDuration(d)} glowColor="blue" delay={0.05 * i} />
                    ))}
                  </div>
                </div>

                {/* Aspect Ratio */}
                <div className="text-center">
                  <h3 className="font-display text-base font-semibold text-white/70 mb-4">Aspect Ratio</h3>
                  <div className="flex items-center justify-center gap-3 flex-wrap">
                    {ASPECT_RATIO_OPTIONS.map((r, i) => (
                      <FloatingChip key={r} label={r} icon="📐" selected={customization.aspectRatio === r} onClick={() => setAspectRatio(r)} glowColor="cyan" delay={0.05 * i} />
                    ))}
                  </div>
                </div>

                {/* Frame Rate */}
                <div className="text-center">
                  <h3 className="font-display text-base font-semibold text-white/70 mb-4">Frame Rate</h3>
                  <div className="flex items-center justify-center gap-3 flex-wrap">
                    {FRAME_RATE_OPTIONS.map((f, i) => (
                      <FloatingChip key={f} label={`${f}fps`} icon="🎞️" selected={customization.frameRate === f} onClick={() => setFrameRate(f)} glowColor="pink" delay={0.05 * i} />
                    ))}
                  </div>
                </div>

                {/* Generate CTA */}
                <div className="text-center pt-4">
                  <motion.button whileHover={{ scale: 1.04, y: -2 }} whileTap={{ scale: 0.96 }} onClick={handleGenerate} className="btn-glow text-base px-10 py-4">
                    <Sparkles className="h-5 w-5" />
                    Generate T2V Prompt
                    <ArrowRight className="h-5 w-5" />
                  </motion.button>
                </div>
              </div>
            )}

            {/* ═══ GENERATING ══════════════════════════════════════════ */}
            {step === "generating" && (
              <div className="flex flex-col items-center gap-6 py-16">
                <motion.div animate={{ rotate: 360 }} transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}>
                  <Sparkles className="h-12 w-12 text-videx-400" />
                </motion.div>
                <div className="text-center">
                  <p className="text-lg font-medium text-white/80">Detractor Engine is crafting your prompt…</p>
                  <p className="mt-1 text-sm text-white/40">
                    Optimizing for physics compliance and <span className="text-videx-300">{customization.selectedStyle}</span> style
                  </p>
                </div>
              </div>
            )}

            {/* ═══ COMPLETE ════════════════════════════════════════════ */}
            {step === "complete" && generatedPrompt && (
              <div className="max-w-3xl mx-auto space-y-6">
                <FloatingCardAnimated delay={0} amplitude={4}>
                  <div className="p-6">
                    {/* Header */}
                    <div className="flex items-center gap-4 mb-4 flex-wrap">
                      <h2 className="font-display text-lg font-bold text-white/90 flex items-center gap-2">
                        <Sparkles className="h-5 w-5 text-videx-400" />
                        Your T2V Prompt
                      </h2>
                      <div className="ml-auto flex items-center gap-3">
                        <span className={cn("text-xs font-mono px-2 py-1 rounded-full border border-border-subtle", scoreColor(generatedPrompt.physics_score))}>
                          Physics: {(generatedPrompt.physics_score * 100).toFixed(0)}%
                        </span>
                        <span className={cn("text-xs font-mono px-2 py-1 rounded-full border border-border-subtle", scoreColor(generatedPrompt.quality_score))}>
                          Quality: {(generatedPrompt.quality_score * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>

                    {/* Prompt text */}
                    <div className="relative rounded-xl bg-surface p-4 border border-border-subtle">
                      <p className="text-sm text-white/70 leading-relaxed font-mono whitespace-pre-wrap">{generatedPrompt.final_prompt}</p>
                    </div>

                    {/* Metadata chips */}
                    <div className="flex flex-wrap gap-2 mt-4">
                      <span className="chip text-xs">{generatedPrompt.prompt_metadata.duration}</span>
                      <span className="chip text-xs">{generatedPrompt.prompt_metadata.aspect_ratio}</span>
                      <span className="chip text-xs">{generatedPrompt.prompt_metadata.frame_rate}fps</span>
                      <span className="chip text-xs">{generatedPrompt.prompt_metadata.selected_style}</span>
                    </div>

                    {/* Camera & lighting info */}
                    <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs text-white/40">
                      <div>
                        <span className="text-white/25 uppercase tracking-wider text-[10px]">Camera</span>
                        <p className="mt-0.5 text-white/50">{generatedPrompt.prompt_metadata.camera_specs}</p>
                      </div>
                      <div>
                        <span className="text-white/25 uppercase tracking-wider text-[10px]">Lighting</span>
                        <p className="mt-0.5 text-white/50">{generatedPrompt.prompt_metadata.lighting_setup}</p>
                      </div>
                      <div>
                        <span className="text-white/25 uppercase tracking-wider text-[10px]">Motion</span>
                        <p className="mt-0.5 text-white/50">{generatedPrompt.prompt_metadata.motion_description}</p>
                      </div>
                      <div>
                        <span className="text-white/25 uppercase tracking-wider text-[10px]">Color Grade</span>
                        <p className="mt-0.5 text-white/50">{generatedPrompt.prompt_metadata.color_grade}</p>
                      </div>
                    </div>

                    {/* Recommended models */}
                    {generatedPrompt.prompt_metadata.recommended_models.length > 0 && (
                      <div className="mt-4 pt-3 border-t border-border-subtle">
                        <span className="text-[10px] text-white/25 uppercase tracking-wider">Recommended for</span>
                        <div className="flex gap-2 mt-1">
                          {generatedPrompt.prompt_metadata.recommended_models.map((m) => (
                            <span key={m} className="text-xs px-2.5 py-1 rounded-full bg-videx-500/10 text-videx-300 border border-videx-500/20">{m}</span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Action buttons */}
                    <div className="flex items-center gap-3 mt-6 pt-4 border-t border-border-subtle flex-wrap">
                      <motion.button whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.96 }} onClick={handleCopy} className="btn-glow text-sm">
                        <Copy className="h-4 w-4" /> Copy Prompt
                      </motion.button>
                      <motion.button whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.96 }} onClick={handleDownload} className="btn-ghost text-sm">
                        <Download className="h-4 w-4" /> Download JSON
                      </motion.button>
                      <motion.button whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.96 }} onClick={resetPipeline} className="btn-ghost text-sm">
                        <RotateCcw className="h-4 w-4" /> New Video
                      </motion.button>
                    </div>

                    {/* Tags */}
                    {generatedPrompt.prompt_metadata.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mt-4 pt-3 border-t border-border-subtle">
                        {generatedPrompt.prompt_metadata.tags.map((tag) => (
                          <span key={tag} className="text-[11px] px-2.5 py-1 rounded-full bg-white/5 text-white/40">#{tag}</span>
                        ))}
                      </div>
                    )}
                  </div>
                </FloatingCardAnimated>
              </div>
            )}

            {/* ═══ ERROR ═══════════════════════════════════════════════ */}
            {step === "error" && (
              <div className="max-w-lg mx-auto text-center py-12">
                <FloatingCardAnimated delay={0} className="border-red-500/20">
                  <div className="p-8">
                    <div className="h-14 w-14 rounded-full bg-red-500/10 flex items-center justify-center mx-auto mb-4">
                      <AlertCircle className="h-7 w-7 text-red-400" />
                    </div>
                    <h3 className="text-lg font-semibold text-white/90 mb-2">Something went wrong</h3>
                    <p className="text-sm text-white/50 mb-6">{errorMessage}</p>
                    <motion.button whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.96 }} onClick={resetPipeline} className="btn-glow">
                      <RotateCcw className="h-4 w-4" /> Try Again
                    </motion.button>
                  </div>
                </FloatingCardAnimated>
              </div>
            )}
          </WeightlessTransition>
        </div>
      </main>
    </div>
  );
}
