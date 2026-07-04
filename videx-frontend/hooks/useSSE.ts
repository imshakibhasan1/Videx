/**
 * useSSE — Server-Sent Events Hook.
 *
 * Connects to the FastAPI SSE endpoint at /api/v1/stream/{jobId}
 * and dispatches parsed events into the Zustand store.
 *
 * Handles:
 *   - Deferred connection until JWT token is confirmed present in localStorage
 *   - Auto-reconnect on network failure (up to 3 retries with exponential backoff)
 *   - Auto-close on terminal events (analysis_complete, prompt_complete, etc.)
 *   - Zustand state updates based on event type
 *   - Cleanup on unmount
 *
 * Token delivery strategy:
 *   The browser's native EventSource API cannot send custom headers.
 *   We therefore append the JWT as a ?token= query parameter, which our
 *   FastAPI `get_current_user` dependency accepts as a fallback after
 *   checking for the Authorization: Bearer header.
 */

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getAnalysisResult } from "@/lib/api";
import { useVidexStore } from "@/store/videx.store";
import type { SSEEvent, SSEEventType } from "@/types/api.types";

// Use the backend URL directly so Next.js doesn't buffer the SSE stream.
// Must NOT go through the /api/v1 proxy for streaming endpoints.
const SSE_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface UseSSEOptions {
  /** Job ID to subscribe to. Null = don't connect. */
  jobId: string | null;
  /** Max reconnection attempts (default: 3). */
  maxRetries?: number;
  /** Called on every received event (for custom handling). */
  onEvent?: (event: SSEEvent) => void;
}

interface UseSSEReturn {
  /** Whether the SSE connection is active. */
  isConnected: boolean;
  /** The last event received. */
  lastEvent: SSEEvent | null;
  /** The last error message. */
  error: string | null;
  /** Manually close the SSE connection. */
  disconnect: () => void;
}

/** Read the JWT from localStorage — safe to call on client only. */
function readToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("videx_access_token");
}

export function useSSE({
  jobId,
  maxRetries = 3,
  onEvent,
}: UseSSEOptions): UseSSEReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState<SSEEvent | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Track the resolved JWT separately so React knows when to (re-)connect.
  const [token, setToken] = useState<string | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);
  const retriesRef = useRef(0);
  // Keep a stable ref to the latest token so the error handler can reconnect
  // with the current token without depending on stale closure values.
  const tokenRef = useRef<string | null>(null);

  const {
    setAnalysisStarted,
    setAnalysisComplete,
    setGenerating,
    setPromptComplete,
    setError: setStoreError,
  } = useVidexStore();

  // ── Resolve the token from localStorage on mount (client only) ───────────
  useEffect(() => {
    const t = readToken();
    tokenRef.current = t;
    setToken(t);

    // If for some reason the token isn't in localStorage yet
    // (e.g. the login page just wrote it and React hasn't re-rendered),
    // poll briefly until we find it.
    if (!t) {
      let attempts = 0;
      const maxAttempts = 20; // 20 × 100ms = 2 seconds max wait
      const poll = setInterval(() => {
        attempts++;
        const found = readToken();
        if (found) {
          tokenRef.current = found;
          setToken(found);
          clearInterval(poll);
        } else if (attempts >= maxAttempts) {
          clearInterval(poll);
          setError("You must be signed in to stream results.");
        }
      }, 100);
      return () => clearInterval(poll);
    }
  }, []);

  // Terminal events that should close the connection
  const TERMINAL_EVENTS: Set<SSEEventType> = new Set([
    "analysis_failed",
    "prompt_complete",
    "prompt_failed",
    "unauthorized",
  ]);

  const handleEvent = useCallback(
    async (sseEvent: SSEEvent) => {
      setLastEvent(sseEvent);
      onEvent?.(sseEvent);

      switch (sseEvent.event) {
        case "analysis_started":
          setAnalysisStarted();
          break;

        case "analysis_complete":
          // Fetch the full analysis result from the API
          if (sseEvent.job_id) {
            try {
              const result = await getAnalysisResult(sseEvent.job_id);
              setAnalysisComplete(result);
            } catch {
              setStoreError("Failed to fetch analysis result.");
            }
          }
          break;

        case "analysis_failed":
          setStoreError(sseEvent.error || "Video analysis failed.");
          break;

        case "prompt_generation_started":
          setGenerating();
          break;

        case "prompt_complete":
          if (sseEvent.prompt_id) {
            const { getPrompt } = await import("@/lib/api");
            try {
              const prompt = await getPrompt(sseEvent.prompt_id);
              setPromptComplete(prompt);
            } catch {
              setStoreError("Failed to fetch generated prompt.");
            }
          }
          break;

        case "prompt_failed":
          setStoreError(sseEvent.error || "Prompt generation failed.");
          break;

        case "unauthorized":
          setStoreError("Session expired. Please log in again.");
          break;

        case "stream_error":
          setError(sseEvent.message || "Stream interrupted.");
          break;
      }
    },
    [
      onEvent,
      setAnalysisStarted,
      setAnalysisComplete,
      setGenerating,
      setPromptComplete,
      setStoreError,
    ]
  );

  const connect = useCallback(
    (resolvedToken: string) => {
      if (!jobId) return;

      // Close any existing connection before opening a new one
      eventSourceRef.current?.close();

      // ── Build the SSE URL with the token as a query param ────────────────
      // EventSource cannot send custom headers, so the token must be in the URL.
      // The backend `get_current_user` dependency accepts ?token= as a fallback.
      const url = `${SSE_BASE_URL}/stream/${jobId}?token=${encodeURIComponent(resolvedToken)}`;

      console.debug("[VIDEX SSE] Connecting to:", url.replace(/token=.+/, "token=<redacted>"));

      const eventSource = new EventSource(url);
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        setIsConnected(true);
        setError(null);
        retriesRef.current = 0;
        console.debug("[VIDEX SSE] Connected for job:", jobId);
      };

      eventSource.onmessage = (messageEvent) => {
        try {
          const data: SSEEvent = JSON.parse(messageEvent.data);
          handleEvent(data);

          // Auto-close on terminal events
          if (TERMINAL_EVENTS.has(data.event)) {
            eventSource.close();
            setIsConnected(false);
          }
        } catch {
          console.warn("[VIDEX SSE] Failed to parse event:", messageEvent.data);
        }
      };

      eventSource.onerror = () => {
        eventSource.close();
        setIsConnected(false);

        // Auto-reconnect with exponential backoff
        if (retriesRef.current < maxRetries) {
          retriesRef.current += 1;
          const backoff = Math.min(1000 * Math.pow(2, retriesRef.current), 10_000);
          console.debug(
            `[VIDEX SSE] Reconnecting in ${backoff}ms (attempt ${retriesRef.current}/${maxRetries})`
          );
          const currentToken = tokenRef.current;
          if (currentToken) {
            setTimeout(() => connect(currentToken), backoff);
          }
        } else {
          setError("Connection lost. Please refresh the page.");
        }
      };
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [jobId, maxRetries, handleEvent]
  );

  const disconnect = useCallback(() => {
    eventSourceRef.current?.close();
    eventSourceRef.current = null;
    setIsConnected(false);
  }, []);

  // ── Connect once BOTH jobId AND token are available ──────────────────────
  // This is the critical guard: we never open EventSource without a valid token.
  useEffect(() => {
    if (!jobId) {
      disconnect();
      return;
    }

    if (!token) {
      // Token not yet resolved — the polling useEffect above will update `token`
      // which will re-trigger this effect.
      console.debug("[VIDEX SSE] Waiting for auth token before connecting…");
      return;
    }

    connect(token);

    return () => {
      disconnect();
    };
  }, [jobId, token, connect, disconnect]);

  return { isConnected, lastEvent, error, disconnect };
}
