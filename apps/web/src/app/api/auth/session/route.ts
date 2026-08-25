import { NextRequest, NextResponse } from "next/server";

import { clearTokenCookies, djangoFetch, setTokenCookies } from "@/lib/server-auth";

export async function GET(request: NextRequest) {
  let access = request.cookies.get("nova_access")?.value;
  const refresh = request.cookies.get("nova_refresh")?.value;
  if (!access && !refresh) {
    return NextResponse.json({ user: null });
  }

  let meResponse = access
    ? await djangoFetch("/auth/me/", { headers: { Authorization: `Bearer ${access}` } })
    : null;
  let refreshed: { access: string; refresh?: string } | null = null;
  if ((!meResponse || meResponse.status === 401) && refresh) {
    const refreshResponse = await djangoFetch("/auth/token/refresh/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh }),
    });
    if (refreshResponse.ok) {
      refreshed = await refreshResponse.json();
      access = refreshed!.access;
      meResponse = await djangoFetch("/auth/me/", {
        headers: { Authorization: `Bearer ${access}` },
      });
    }
  }
  if (!meResponse?.ok) {
    const response = NextResponse.json({ user: null });
    clearTokenCookies(response);
    return response;
  }
  const response = NextResponse.json({ user: await meResponse.json() });
  if (refreshed) setTokenCookies(response, refreshed);
  return response;
}
