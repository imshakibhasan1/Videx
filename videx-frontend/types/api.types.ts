/**
 * VIDEX API Type Definitions.
 *
 * These types mirror the Pydantic schemas from the FastAPI backend.
 * In production, auto-generate these from the OpenAPI spec.
 */

// ── Auth ────────────────────────────────────────────────────────────────────

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserProfile {
  id: string;
  email: string;
  name: string | null;
  avatar_url: string | null;
  provider: string;
  is_verified: boolean;
}

// ── Upload ──────────────────────────────────────────────────────────────────

export interface SignatureRequest {
  filename: string;
  content_type: string;
}

export interface SignatureResponse {
  signature: string;
  timestamp: number;
  api_key: string;
  cloud_name: string;
  folder: string;
  upload_url: string;
  public_id: string;
  job_id: string;
}

export interface UploadConfirmRequest {
  job_id: string;
  cloudinary_public_id: string;
  cloudinary_secure_url: string;
  video_duration: number;
  video_size_bytes: number;
  video_format: string;
}

export interface UploadConfirmResponse {
  job_id: string;
  status: string;
  message: string;
  celery_task_id: string | null;
}

// ── Analysis (Step 1) ───────────────────────────────────────────────────────

export interface PhysicalProperties {
  lighting: string;
  camera_angle: string;
  depth_of_field: string;
  motion_blur: string;
  color_temperature: string;
  environment: string;
  time_of_day: string;
  weather_conditions: string;
  dominant_colors: string;
  subject_motion: string;
  camera_motion: string;
}

export interface StyleOption {
  id: "original" | "cinematic" | "documentary";
  label: string;
  description: string;
  mood_tags: string[];
  color_grading: string;
  camera_movement: string;
  lighting_recipe: string;
}

export interface PhysicsFlags {
  gravity_compliance: string;
  fluid_dynamics: string;
  lighting_physics: string;
  motion_physics: string;
}

export interface TechnicalMetadata {
  estimated_codec: string;
  aspect_ratio_detected: string;
  estimated_frame_rate: number;
  video_quality: "Excellent" | "Good" | "Fair" | "Poor";
  recommended_models: string[];
}

export interface AnalysisResult {
  analysis_id: string;
  job_id: string;
  scene_summary: string;
  physical_properties: PhysicalProperties;
  style_options: StyleOption[];
  physics_flags: PhysicsFlags;
  technical_metadata: TechnicalMetadata;
  confidence_score: number;
}

// ── Prompt (Step 2 & 3) ──────────────────────────────────────────────────────

export type StyleChoice = "original" | "cinematic" | "documentary";
export type DurationChoice = "8s" | "10s" | "15s";
export type AspectRatioChoice = "16:9" | "9:16" | "1:1";
export type FrameRateChoice = 24 | 30 | 60;

export interface GeneratePromptRequest {
  job_id: string;
  analysis_id: string;
  selected_style: StyleChoice;
  duration: DurationChoice;
  aspect_ratio: AspectRatioChoice;
  frame_rate: FrameRateChoice;
  custom_overrides?: Record<string, string>;
}

export interface TemporalBeat {
  beat: number;
  timecode: string;
  description: string;
}

export interface PromptMetadata {
  duration: string;
  aspect_ratio: string;
  frame_rate: number;
  selected_style: string;
  camera_specs: string;
  lighting_setup: string;
  motion_description: string;
  color_grade: string;
  physics_notes: string[];
  temporal_structure: TemporalBeat[];
  recommended_models: string[];
  tags: string[];
}

export interface GeneratedPrompt {
  prompt_id: string;
  job_id: string;
  config_id: string;
  final_prompt: string;
  prompt_metadata: PromptMetadata;
  physics_score: number;
  quality_score: number;
  share_token: string | null;
  is_public: boolean;
  copy_count: number;
  created_at: string;
}

// ── SSE Events ──────────────────────────────────────────────────────────────

export type SSEEventType =
  | "analysis_started"
  | "analysis_complete"
  | "analysis_failed"
  | "prompt_generation_started"
  | "prompt_complete"
  | "prompt_failed"
  | "unauthorized"
  | "stream_error";

export interface SSEEvent {
  event: SSEEventType;
  job_id?: string;
  analysis_id?: string;
  prompt_id?: string;
  confidence_score?: number;
  physics_score?: number;
  quality_score?: number;
  error?: string;
  message?: string;
}

// ── Common ──────────────────────────────────────────────────────────────────

export interface ApiError {
  error: string;
  message: string;
  detail: string | null;
}

export interface PromptListResponse {
  items: GeneratedPrompt[];
  total: number;
  page: number;
  per_page: number;
}
