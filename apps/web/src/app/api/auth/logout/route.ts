import { NextRequest, NextResponse } from "next/server";

import { clearTokenCookies, djangoFetch } from "@/lib/server-auth";

export async function POST(request: NextRequest) {
  const refresh = request.cookies.get("nova_refresh")?.value;
  if (refresh) {
    try {
      await djangoFetch("/auth/logout/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh }),
      });
    } catch {
      // Local logout must still succeed when the API is temporarily unavailable.
    }
  }
  const response = NextResponse.json({ ok: true });
  clearTokenCookies(response);
  return response;
}
