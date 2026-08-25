import { NextResponse } from "next/server";

export const DJANGO_API_URL = (process.env.API_URL ?? "http://127.0.0.1:8000/api/v1").replace(/\/$/, "");

type TokenPair = { access: string; refresh?: string };

export function setTokenCookies(response: NextResponse, tokens: TokenPair) {
  const secure = process.env.NODE_ENV === "production";
  response.cookies.set("nova_access", tokens.access, {
    httpOnly: true,
    secure,
    sameSite: "strict",
    path: "/",
    maxAge: 15 * 60,
  });
  if (tokens.refresh) {
    response.cookies.set("nova_refresh", tokens.refresh, {
      httpOnly: true,
      secure,
      sameSite: "strict",
      path: "/",
      maxAge: 7 * 24 * 60 * 60,
    });
  }
}

export function clearTokenCookies(response: NextResponse) {
  response.cookies.set("nova_access", "", { httpOnly: true, path: "/", maxAge: 0 });
  response.cookies.set("nova_refresh", "", { httpOnly: true, path: "/", maxAge: 0 });
}

export async function djangoFetch(path: string, init?: RequestInit) {
  return fetch(`${DJANGO_API_URL}${path}`, { cache: "no-store", ...init });
}
