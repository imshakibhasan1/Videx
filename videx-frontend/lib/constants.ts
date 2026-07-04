/**
 * VIDEX App Constants.
 */

export const APP_NAME = "VIDEX";
export const APP_DESCRIPTION = "AI-Powered Video Reverse-Engineering Platform";

/** API base URL — proxied through Next.js rewrites in development. */
export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

/** Cloudinary cloud name for direct uploads. */
export const CLOUDINARY_CLOUD = process.env.NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME || "";

/** Upload constraints (must match backend .env values) */
export const UPLOAD = {
  MAX_SIZE_BYTES: 52_428_800,  // 50 MB
  MAX_SIZE_LABEL: "50 MB",
  MAX_DURATION: 15,            // 15 seconds
  ACCEPTED_TYPES: {
    "video/mp4": [".mp4"],
    "video/quicktime": [".mov"],
    "video/webm": [".webm"],
    "video/x-msvideo": [".avi"],
  } as Record<string, string[]>,
} as const;

/** Step 2 selectable options */
export const DURATION_OPTIONS = ["8s", "10s", "15s"] as const;
export const ASPECT_RATIO_OPTIONS = ["16:9", "9:16", "1:1"] as const;
export const FRAME_RATE_OPTIONS = [24, 30, 60] as const;

/** Style option display config */
export const STYLE_CONFIG = {
  original: {
    icon: "🎬",
    gradient: "from-amber-500/20 to-orange-500/20",
    glowClass: "shadow-glow-blue",
    borderActive: "border-amber-400/40",
  },
  cinematic: {
    icon: "🎥",
    gradient: "from-videx-500/20 to-blue-500/20",
    glowClass: "shadow-glow-purple",
    borderActive: "border-videx-400/40",
  },
  documentary: {
    icon: "📹",
    gradient: "from-cyan-500/20 to-teal-500/20",
    glowClass: "shadow-glow-cyan",
    borderActive: "border-cyan-400/40",
  },
} as const;
