export class ApiError extends Error {
  constructor(public status: number, public payload: unknown) {
    super(typeof payload === "object" && payload && "detail" in payload ? String(payload.detail) : "تعذر إكمال الطلب");
  }
}

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/nova${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
  });
  const text = await response.text();
  const payload = text ? JSON.parse(text) : null;
  if (!response.ok) throw new ApiError(response.status, payload);
  return payload as T;
}

export function errorMessage(error: unknown) {
  if (error instanceof ApiError) {
    if (typeof error.payload === "object" && error.payload) {
      return Object.values(error.payload as Record<string, unknown>).flat().join(" ");
    }
    return error.message;
  }
  return "حدث خطأ غير متوقع. حاول مرة أخرى.";
}

export function formatMoney(cents: number, currency = "SAR", locale = "ar-SA") {
  return new Intl.NumberFormat(locale, { style: "currency", currency }).format(cents / 100);
}
