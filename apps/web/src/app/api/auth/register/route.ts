import { NextRequest, NextResponse } from "next/server";

import { djangoFetch, setTokenCookies } from "@/lib/server-auth";

export async function POST(request: NextRequest) {
  const registration = await request.json();
  const registerResponse = await djangoFetch("/auth/register/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(registration),
  });
  const registered = await registerResponse.json();
  if (!registerResponse.ok) {
    return NextResponse.json(registered, { status: registerResponse.status });
  }
  const tokenResponse = await djangoFetch("/auth/token/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: registration.username, password: registration.password }),
  });
  const tokens = (await tokenResponse.json()) as { access: string; refresh: string };
  const response = NextResponse.json({ user: registered }, { status: 201 });
  setTokenCookies(response, tokens);
  return response;
}
