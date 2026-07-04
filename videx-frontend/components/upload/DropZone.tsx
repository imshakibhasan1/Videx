/**
 * DropZone — Video Upload Component.
 *
 * Drag-and-drop or click-to-browse file picker with:
 * - Animated border pulse on drag-over
 * - File validation (type + size)
 * - Upload progress bar
 * - Video preview thumbnail
 */

"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, Film, X, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { UPLOAD } from "@/lib/constants";
import { formatFileSize } from "@/lib/utils";
import { useUpload } from "@/hooks/useUpload";

export function DropZone() {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const { startUpload, cancelUpload, isUploading, progress, error } = useUpload();

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (!file) return;

      // Generate video preview
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);

      await startUpload(file);
    },
    [startUpload]
  );

  const { getRootProps, getInputProps, isDragActive, fileRejections } =
    useDropzone({
      onDrop,
      accept: UPLOAD.ACCEPTED_TYPES,
      maxSize: UPLOAD.MAX_SIZE_BYTES,
      maxFiles: 1,
      disabled: isUploading,
      multiple: false,
    });

  const rejectionError = fileRejections[0]?.errors[0]?.message;
  const displayError = error || rejectionError;

  const handleClear = useCallback(() => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    cancelUpload();
  }, [previewUrl, cancelUpload]);

  return (
    <div className="w-full max-w-2xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
      >
        {/* ── Drop Zone Area ───────────────────────────────────────────── */}
        <div
          {...getRootProps()}
          className={cn(
            "relative flex flex-col items-center justify-center",
            "min-h-[260px] rounded-3xl p-8",
            "border-2 border-dashed transition-all duration-400 ease-out-expo",
            "cursor-pointer group",
            // Default state
            !isDragActive && !isUploading && !displayError && [
              "border-border-medium bg-surface-glass",
              "hover:border-videx-500/40 hover:bg-surface-glass-hover",
              "hover:shadow-float-md",
            ],
            // Drag active state
            isDragActive && [
              "border-videx-400 bg-videx-500/10",
              "shadow-glow-purple",
            ],
            // Uploading state
            isUploading && "border-videx-500/30 bg-surface-glass cursor-default",
            // Error state
            displayError && "border-red-500/40 bg-red-500/5",
          )}
        >
          <input {...getInputProps()} />

          <AnimatePresence mode="wait">
            {/* ── Uploading State ────────────────────────────────────── */}
            {isUploading ? (
              <motion.div
                key="uploading"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="flex flex-col items-center gap-4 w-full"
              >
                {/* Preview */}
                {previewUrl && (
                  <video
                    src={previewUrl}
                    className="w-48 h-28 object-cover rounded-xl border border-border-subtle"
                    muted
                    playsInline
                  />
                )}

                {/* Progress bar */}
                <div className="w-full max-w-sm">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-white/60">Uploading to CDN…</span>
                    <span className="text-sm font-mono text-videx-300">{progress}%</span>
                  </div>
                  <div className="h-2 rounded-full bg-white/5 overflow-hidden">
                    <motion.div
                      className="h-full rounded-full bg-gradient-to-r from-videx-500 to-blue-500"
                      initial={{ width: 0 }}
                      animate={{ width: `${progress}%` }}
                      transition={{ duration: 0.3, ease: "easeOut" }}
                    />
                  </div>
                </div>

                {/* Cancel */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleClear();
                  }}
                  className="text-xs text-white/40 hover:text-white/70 transition-colors"
                >
                  Cancel
                </button>
              </motion.div>
            ) : (
              /* ── Idle / Drag State ──────────────────────────────── */
              <motion.div
                key="idle"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="flex flex-col items-center gap-4"
              >
                <motion.div
                  animate={isDragActive ? { scale: 1.15, y: -8 } : { scale: 1, y: 0 }}
                  transition={{ type: "spring", stiffness: 300, damping: 20 }}
                  className={cn(
                    "flex items-center justify-center",
                    "h-16 w-16 rounded-2xl",
                    "bg-videx-500/10 border border-videx-500/20",
                    "transition-colors duration-300",
                    isDragActive && "bg-videx-500/20 border-videx-400/40",
                  )}
                >
                  {isDragActive ? (
                    <Film className="h-7 w-7 text-videx-300" />
                  ) : (
                    <Upload className="h-7 w-7 text-videx-400 group-hover:text-videx-300 transition-colors" />
                  )}
                </motion.div>

                <div className="text-center">
                  <p className="text-base font-medium text-white/80">
                    {isDragActive ? "Drop your video here" : "Drag & drop a video file"}
                  </p>
                  <p className="mt-1 text-sm text-white/40">
                    or <span className="text-videx-400 underline underline-offset-2">browse files</span>
                  </p>
                </div>

                <div className="flex items-center gap-4 mt-1">
                  <span className="text-xs text-white/30">MP4 · MOV · WebM · AVI</span>
                  <span className="text-xs text-white/20">|</span>
                  <span className="text-xs text-white/30">Max {UPLOAD.MAX_SIZE_LABEL} · {UPLOAD.MAX_DURATION}s</span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* ── Error Message ──────────────────────────────────────────── */}
        <AnimatePresence>
          {displayError && (
            <motion.div
              initial={{ opacity: 0, y: -8, height: 0 }}
              animate={{ opacity: 1, y: 0, height: "auto" }}
              exit={{ opacity: 0, y: -8, height: 0 }}
              className="mt-3 flex items-center gap-2 text-sm text-red-400"
            >
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
              <span>{displayError}</span>
              <button onClick={handleClear} className="ml-auto">
                <X className="h-4 w-4 text-red-400/60 hover:text-red-300" />
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}
