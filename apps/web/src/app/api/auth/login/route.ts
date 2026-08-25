import { NextRequest, NextResponse } from "next/server";

import { djangoFetch, setTokenCookies } from "@/lib/server-auth";

export async function POST(request: NextRequest) {
  const credentials = await request.json();
  const tokenResponse = await djangoFetch("/auth/token/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(credentials),
  });
  if (!tokenResponse.ok) {
    return NextResponse.json(
      { detail: "اسم المستخدم أو كلمة المرور غير صحيحة." },
      { status: tokenResponse.status },
    );
  }
  const tokens = (await tokenResponse.json()) as { access: string; refresh: string };
  const meResponse = await djangoFetch("/auth/me/", {
    headers: { Authorization: `Bearer ${tokens.access}` },
  });
  const response = NextResponse.json({ user: await meResponse.json() });
  setTokenCookies(response, tokens);
  return response;
}
