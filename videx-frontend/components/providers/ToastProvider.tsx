/**
 * Toaster Provider — wraps the Sonner toast system.
 */

"use client";

import { Toaster as SonnerToaster } from "sonner";

export function ToastProvider() {
  return (
    <SonnerToaster
      position="bottom-right"
      toastOptions={{
        style: {
          background: "rgba(22, 22, 38, 0.95)",
          border: "1px solid rgba(255,255,255,0.08)",
          color: "#fff",
          backdropFilter: "blur(12px)",
          fontFamily: "var(--font-inter)",
        },
        className: "shadow-float-md",
      }}
      theme="dark"
      richColors
      closeButton
    />
  );
}
