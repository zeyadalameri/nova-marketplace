import { NextRequest, NextResponse } from "next/server";

import { djangoFetch, refreshTokenPair, setTokenCookies } from "@/lib/server-auth";

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
    refreshed = await refreshTokenPair(refresh);
    if (refreshed) {
      access = refreshed!.access;
      meResponse = await djangoFetch("/auth/me/", {
        headers: { Authorization: `Bearer ${access}` },
      });
    }
  }
  if (!meResponse?.ok) {
    // Do not clear cookies from a stale failed request; a newer login/refresh may already
    // have replaced them in another response. Explicit logout remains responsible for clearing.
    return NextResponse.json({ user: null });
  }
  const response = NextResponse.json({ user: await meResponse.json() });
  if (refreshed) setTokenCookies(response, refreshed);
  return response;
}
