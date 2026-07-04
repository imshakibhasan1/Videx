/**
 * Dashboard layout — guards the route behind authentication.
 *
 * If no JWT token is found in localStorage, the user is immediately
 * redirected to /login before any dashboard content is rendered.
 * This prevents the upload flow from running without auth, which
 * would cause the SSE stream to fire with no token.
 */
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("videx_access_token");
    if (!token) {
      router.replace("/login");
    } else {
      setIsReady(true);
    }
  }, [router]);

  // Render nothing while we check — avoids flash of dashboard content
  if (!isReady) return null;

  return <>{children}</>;
}
