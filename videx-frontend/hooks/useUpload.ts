/**
 * useUpload — Cloudinary Direct Upload Hook.
 *
 * Orchestrates the full two-phase upload flow:
 *   1. Request signed upload params from FastAPI
 *   2. Upload the file directly from browser → Cloudinary CDN
 *   3. Confirm the upload back to FastAPI
 *   4. Automatically trigger analysis via the backend
 *
 * Integrates directly with the Zustand store for state management.
 */

"use client";

import { useCallback, useRef, useState } from "react";
import {
  confirmUpload,
  getUploadSignature,
  uploadToCloudinary,
} from "@/lib/api";
import { UPLOAD } from "@/lib/constants";
import { useVidexStore } from "@/store/videx.store";
import type { ApiError } from "@/types/api.types";

interface UseUploadReturn {
  /** Start the upload process with the selected file. */
  startUpload: (file: File) => Promise<void>;
  /** Abort an in-progress upload. */
  cancelUpload: () => void;
  /** Whether an upload is currently in progress. */
  isUploading: boolean;
  /** Upload progress percentage (0–100). */
  progress: number;
  /** Error message if upload failed. */
  error: string | null;
}

export function useUpload(): UseUploadReturn {
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef(false);

  const {
    setFile,
    setUploadProgress,
    setUploadComplete,
    setError: setStoreError,
    setAnalysisStarted,
  } = useVidexStore();

  const startUpload = useCallback(
    async (file: File) => {
      // ── Pre-flight validation ────────────────────────────────────────
      setError(null);
      abortRef.current = false;

      // File size check
      if (file.size > UPLOAD.MAX_SIZE_BYTES) {
        const msg = `File exceeds ${UPLOAD.MAX_SIZE_LABEL} limit.`;
        setError(msg);
        setStoreError(msg);
        return;
      }

      // MIME type check
      const allowedTypes = Object.keys(UPLOAD.ACCEPTED_TYPES);
      if (!allowedTypes.includes(file.type)) {
        const msg = `Unsupported format: ${file.type}. Use MP4, MOV, WebM, or AVI.`;
        setError(msg);
        setStoreError(msg);
        return;
      }

      setIsUploading(true);
      setProgress(0);
      setFile(file); // Push to Zustand → triggers "uploading" step

      try {
        // ── Phase 1: Get signed params from FastAPI ────────────────────
        const signatureData = await getUploadSignature({
          filename: file.name,
          content_type: file.type,
        });

        if (abortRef.current) return;

        // ── Phase 2: Direct upload to Cloudinary CDN ──────────────────
        const cloudinaryResult = await uploadToCloudinary(
          file,
          signatureData,
          (percent) => {
            setProgress(percent);
            setUploadProgress(percent);
          }
        );

        if (abortRef.current) return;

        // ── Validate duration client-side ──────────────────────────────
        if (cloudinaryResult.duration > UPLOAD.MAX_DURATION) {
          const msg = `Video duration (${cloudinaryResult.duration.toFixed(1)}s) exceeds the ${UPLOAD.MAX_DURATION}s limit.`;
          setError(msg);
          setStoreError(msg);
          return;
        }

        // ── Phase 3: Confirm upload with FastAPI ──────────────────────
        const confirmation = await confirmUpload({
          job_id: signatureData.job_id,
          cloudinary_public_id: cloudinaryResult.public_id,
          cloudinary_secure_url: cloudinaryResult.secure_url,
          video_duration: cloudinaryResult.duration,
          video_size_bytes: cloudinaryResult.bytes,
          video_format: cloudinaryResult.format,
        });

        if (abortRef.current) return;

        // ── Success: update Zustand store ──────────────────────────────
        setUploadComplete({
          jobId: signatureData.job_id,
          cloudinaryUrl: cloudinaryResult.secure_url,
          cloudinaryPublicId: cloudinaryResult.public_id,
          videoDuration: cloudinaryResult.duration,
        });

        // Automatically transition to analysis step
        setAnalysisStarted();
      } catch (err) {
        const apiErr = err as ApiError;
        const msg = apiErr?.message || "Upload failed. Please try again.";
        setError(msg);
        setStoreError(msg);
      } finally {
        setIsUploading(false);
      }
    },
    [setFile, setUploadProgress, setUploadComplete, setStoreError, setAnalysisStarted]
  );

  const cancelUpload = useCallback(() => {
    abortRef.current = true;
    setIsUploading(false);
    setProgress(0);
  }, []);

  return { startUpload, cancelUpload, isUploading, progress, error };
}
