import { NextRequest, NextResponse } from "next/server";

import { DJANGO_API_URL, refreshTokenPair, setTokenCookies } from "@/lib/server-auth";

type RouteContext = { params: Promise<{ path: string[] }> };

async function proxy(request: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  const target = `${DJANGO_API_URL}/${path.join("/")}/${request.nextUrl.search}`;
  const method = request.method;
  const body = method === "GET" || method === "HEAD" ? undefined : await request.arrayBuffer();
  const buildHeaders = (access?: string) => {
    const headers = new Headers();
    headers.set("Accept", "application/json");
    const contentType = request.headers.get("content-type");
    if (contentType) headers.set("Content-Type", contentType);
    if (access) headers.set("Authorization", `Bearer ${access}`);
    const idempotencyKey = request.headers.get("idempotency-key");
    if (idempotencyKey) headers.set("Idempotency-Key", idempotencyKey);
    return headers;
  };

  try {
    let access = request.cookies.get("nova_access")?.value;
    let upstream = await fetch(target, { method, headers: buildHeaders(access), body, cache: "no-store" });
    let refreshed: { access: string; refresh?: string } | null = null;
    if (upstream.status === 401 && request.cookies.get("nova_refresh")?.value) {
      refreshed = await refreshTokenPair(request.cookies.get("nova_refresh")!.value);
      if (refreshed) {
        access = refreshed!.access;
        upstream = await fetch(target, {
          method,
          headers: buildHeaders(access),
          body,
          cache: "no-store",
        });
      }
    }
    const response = new NextResponse(await upstream.arrayBuffer(), {
      status: upstream.status,
      headers: { "Content-Type": upstream.headers.get("content-type") ?? "application/json" },
    });
    if (refreshed) setTokenCookies(response, refreshed);
    return response;
  } catch {
    return NextResponse.json(
      { detail: "خدمة المتجر غير متاحة مؤقتًا. تأكد أن خادم Django يعمل." },
      { status: 503 },
    );
  }
}

export const GET = proxy;
export const POST = proxy;
export const PATCH = proxy;
export const PUT = proxy;
export const DELETE = proxy;
