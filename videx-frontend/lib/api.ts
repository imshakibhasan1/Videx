/**
 * VIDEX Typed API Client.
 *
 * Centralized HTTP client for all FastAPI backend calls.
 * Handles token injection, error normalization, and response typing.
 */

import axios, { AxiosError, type AxiosInstance, type AxiosRequestConfig } from "axios";
import type {
  AnalysisResult,
  ApiError,
  GeneratedPrompt,
  GeneratePromptRequest,
  LoginRequest,
  PromptListResponse,
  RegisterRequest,
  SignatureRequest,
  SignatureResponse,
  TokenResponse,
  UploadConfirmRequest,
  UploadConfirmResponse,
  UserProfile,
} from "@/types/api.types";
import { API_BASE } from "@/lib/constants";

// ── Axios Instance ──────────────────────────────────────────────────────────

const client: AxiosInstance = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
  timeout: 30_000,
});

// ── Request interceptor: attach JWT ─────────────────────────────────────────
client.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("videx_access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// ── Response interceptor: normalize errors ──────────────────────────────────
client.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    const apiError: ApiError = error.response?.data || {
      error: "NETWORK_ERROR",
      message: error.message || "An unexpected error occurred.",
      detail: null,
    };
    return Promise.reject(apiError);
  }
);

// ── Auth ────────────────────────────────────────────────────────────────────

export async function register(data: RegisterRequest): Promise<TokenResponse> {
  const res = await client.post<TokenResponse>("/auth/register", data);
  return res.data;
}

export async function login(data: LoginRequest): Promise<TokenResponse> {
  const res = await client.post<TokenResponse>("/auth/login", data);
  return res.data;
}

export async function refreshToken(refresh_token: string): Promise<TokenResponse> {
  const res = await client.post<TokenResponse>("/auth/refresh", { refresh_token });
  return res.data;
}

export async function getMe(): Promise<UserProfile> {
  const res = await client.get<UserProfile>("/auth/me");
  return res.data;
}

// ── Upload ──────────────────────────────────────────────────────────────────

export async function getUploadSignature(data: SignatureRequest): Promise<SignatureResponse> {
  const res = await client.post<SignatureResponse>("/upload/signature", data);
  return res.data;
}

export async function confirmUpload(data: UploadConfirmRequest): Promise<UploadConfirmResponse> {
  const res = await client.post<UploadConfirmResponse>("/upload/confirm", data);
  return res.data;
}

// ── Analysis ────────────────────────────────────────────────────────────────

export async function getAnalysisResult(jobId: string): Promise<AnalysisResult> {
  const res = await client.get<AnalysisResult>(`/analyze/${jobId}`);
  return res.data;
}

// ── Prompts ─────────────────────────────────────────────────────────────────

export async function generatePrompt(data: GeneratePromptRequest): Promise<{ job_id: string; config_id: string; status: string; stream_url: string }> {
  const res = await client.post("/prompts/generate", data);
  return res.data;
}

export async function getPrompt(promptId: string): Promise<GeneratedPrompt> {
  const res = await client.get<GeneratedPrompt>(`/prompts/${promptId}`);
  return res.data;
}

export async function listPrompts(page = 1, perPage = 20): Promise<PromptListResponse> {
  const res = await client.get<PromptListResponse>("/prompts/", { params: { page, per_page: perPage } });
  return res.data;
}

export async function togglePromptShare(promptId: string, isPublic: boolean): Promise<{ share_url: string | null; share_token: string | null }> {
  const res = await client.post(`/prompts/${promptId}/share`, { is_public: isPublic });
  return res.data;
}

export async function trackCopy(promptId: string): Promise<void> {
  await client.post(`/prompts/${promptId}/copy`);
}

export async function getPublicPrompt(shareToken: string): Promise<GeneratedPrompt> {
  const res = await client.get<GeneratedPrompt>(`/prompts/public/${shareToken}`);
  return res.data;
}

// ── Direct Cloudinary Upload ────────────────────────────────────────────────

export async function uploadToCloudinary(
  file: File,
  signatureData: SignatureResponse,
  onProgress?: (percent: number) => void
): Promise<{ secure_url: string; public_id: string; duration: number; bytes: number; format: string }> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("api_key", signatureData.api_key);
  formData.append("timestamp", String(signatureData.timestamp));
  formData.append("signature", signatureData.signature);
  formData.append("public_id", signatureData.public_id);
  formData.append("folder", signatureData.folder);
  formData.append("resource_type", "video");

  const res = await axios.post(signatureData.upload_url, formData, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 120_000,
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percent);
      }
    },
  });

  return {
    secure_url: res.data.secure_url,
    public_id: res.data.public_id,
    duration: res.data.duration || 0,
    bytes: res.data.bytes || 0,
    format: res.data.format || "mp4",
  };
}

export default client;
