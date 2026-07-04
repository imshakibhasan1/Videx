/**
 * VIDEX Global State Store (Zustand 5).
 *
 * Manages the full lifecycle state across all 3 pipeline steps:
 *   Upload → Analysis → Customization → Prompt Generation
 *
 * This single store replaces what would be ~5 React contexts.
 */

import { create } from "zustand";
import { devtools } from "zustand/middleware";
import type {
  AnalysisResult,
  AspectRatioChoice,
  DurationChoice,
  FrameRateChoice,
  GeneratedPrompt,
  StyleChoice,
} from "@/types/api.types";

// ── Pipeline Step ───────────────────────────────────────────────────────────

export type PipelineStep =
  | "idle"           // No upload yet
  | "uploading"      // File being uploaded to Cloudinary
  | "upload_done"    // Upload confirmed, waiting for analysis to be triggered
  | "analyzing"      // MiMo V2.5 processing the video
  | "analysis_done"  // Step 1 complete — showing results
  | "customizing"    // User selecting Step 2 options
  | "generating"     // Step 3 Detractor Engine running
  | "complete"       // Final prompt ready
  | "error";         // Something failed

// ── Upload State ────────────────────────────────────────────────────────────

interface UploadState {
  file: File | null;
  fileName: string | null;
  fileSize: number;
  progress: number;       // 0–100
  jobId: string | null;
  cloudinaryUrl: string | null;
  cloudinaryPublicId: string | null;
  videoDuration: number;
}

// ── Customization State (Step 2 user selections) ────────────────────────────

interface CustomizationState {
  selectedStyle: StyleChoice;
  duration: DurationChoice;
  aspectRatio: AspectRatioChoice;
  frameRate: FrameRateChoice;
}

// ── Store Shape ─────────────────────────────────────────────────────────────

interface VidexState {
  // Pipeline
  step: PipelineStep;
  errorMessage: string | null;

  // Upload (Step 0)
  upload: UploadState;

  // Analysis (Step 1)
  analysis: AnalysisResult | null;

  // Customization (Step 2)
  customization: CustomizationState;

  // Generated Prompt (Step 3)
  generatedPrompt: GeneratedPrompt | null;

  // ── Actions ──────────────────────────────────────────────────────────────

  // Pipeline control
  setStep: (step: PipelineStep) => void;
  setError: (message: string) => void;
  resetPipeline: () => void;

  // Upload actions
  setFile: (file: File) => void;
  setUploadProgress: (progress: number) => void;
  setUploadComplete: (data: {
    jobId: string;
    cloudinaryUrl: string;
    cloudinaryPublicId: string;
    videoDuration: number;
  }) => void;

  // Analysis actions
  setAnalysisStarted: () => void;
  setAnalysisComplete: (result: AnalysisResult) => void;

  // Customization actions
  setSelectedStyle: (style: StyleChoice) => void;
  setDuration: (duration: DurationChoice) => void;
  setAspectRatio: (ratio: AspectRatioChoice) => void;
  setFrameRate: (rate: FrameRateChoice) => void;

  // Prompt actions
  setGenerating: () => void;
  setPromptComplete: (prompt: GeneratedPrompt) => void;
}

// ── Initial values ──────────────────────────────────────────────────────────

const initialUpload: UploadState = {
  file: null,
  fileName: null,
  fileSize: 0,
  progress: 0,
  jobId: null,
  cloudinaryUrl: null,
  cloudinaryPublicId: null,
  videoDuration: 0,
};

const initialCustomization: CustomizationState = {
  selectedStyle: "original",
  duration: "8s",
  aspectRatio: "16:9",
  frameRate: 24,
};

// ── Store Creation ──────────────────────────────────────────────────────────

export const useVidexStore = create<VidexState>()(
  devtools(
    (set) => ({
      // ── Initial state ──────────────────────────────────────────────────
      step: "idle",
      errorMessage: null,
      upload: initialUpload,
      analysis: null,
      customization: initialCustomization,
      generatedPrompt: null,

      // ── Pipeline control ───────────────────────────────────────────────
      setStep: (step) => set({ step, errorMessage: null }, false, "setStep"),

      setError: (message) =>
        set({ step: "error", errorMessage: message }, false, "setError"),

      resetPipeline: () =>
        set(
          {
            step: "idle",
            errorMessage: null,
            upload: initialUpload,
            analysis: null,
            customization: initialCustomization,
            generatedPrompt: null,
          },
          false,
          "resetPipeline"
        ),

      // ── Upload ─────────────────────────────────────────────────────────
      setFile: (file) =>
        set(
          {
            step: "uploading",
            upload: {
              ...initialUpload,
              file,
              fileName: file.name,
              fileSize: file.size,
            },
          },
          false,
          "setFile"
        ),

      setUploadProgress: (progress) =>
        set(
          (state) => ({ upload: { ...state.upload, progress } }),
          false,
          "setUploadProgress"
        ),

      setUploadComplete: ({ jobId, cloudinaryUrl, cloudinaryPublicId, videoDuration }) =>
        set(
          (state) => ({
            step: "upload_done",
            upload: {
              ...state.upload,
              progress: 100,
              jobId,
              cloudinaryUrl,
              cloudinaryPublicId,
              videoDuration,
            },
          }),
          false,
          "setUploadComplete"
        ),

      // ── Analysis ───────────────────────────────────────────────────────
      setAnalysisStarted: () =>
        set({ step: "analyzing" }, false, "setAnalysisStarted"),

      setAnalysisComplete: (result) =>
        set(
          { step: "analysis_done", analysis: result },
          false,
          "setAnalysisComplete"
        ),

      // ── Customization ──────────────────────────────────────────────────
      setSelectedStyle: (selectedStyle) =>
        set(
          (state) => ({
            step: "customizing",
            customization: { ...state.customization, selectedStyle },
          }),
          false,
          "setSelectedStyle"
        ),

      setDuration: (duration) =>
        set(
          (state) => ({
            step: "customizing",
            customization: { ...state.customization, duration },
          }),
          false,
          "setDuration"
        ),

      setAspectRatio: (aspectRatio) =>
        set(
          (state) => ({
            step: "customizing",
            customization: { ...state.customization, aspectRatio },
          }),
          false,
          "setAspectRatio"
        ),

      setFrameRate: (frameRate) =>
        set(
          (state) => ({
            step: "customizing",
            customization: { ...state.customization, frameRate },
          }),
          false,
          "setFrameRate"
        ),

      // ── Prompt Generation ──────────────────────────────────────────────
      setGenerating: () =>
        set({ step: "generating" }, false, "setGenerating"),

      setPromptComplete: (prompt) =>
        set(
          { step: "complete", generatedPrompt: prompt },
          false,
          "setPromptComplete"
        ),
    }),
    { name: "videx-store" }
  )
);
