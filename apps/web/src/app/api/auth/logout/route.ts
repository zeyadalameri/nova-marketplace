import { NextResponse } from "next/server";

import { clearTokenCookies } from "@/lib/server-auth";

export async function POST() {
  const response = NextResponse.json({ ok: true });
  clearTokenCookies(response);
  return response;
}
