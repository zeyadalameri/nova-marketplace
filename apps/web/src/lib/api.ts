export type Category = {
  id: number;
  name: string;
  name_en: string;
  slug: string;
  description: string;
  description_en: string;
  image_url: string;
  display_order: number;
};

export type Product = {
  id: number;
  name: string;
  name_en: string;
  slug: string;
  brand: string;
  sku: string;
  description: string;
  description_en: string;
  price_cents: number;
  price: string;
  currency: string;
  stock: number;
  image_url: string;
  is_featured: boolean;
  is_available: boolean;
  category: Category;
};

type PaginatedResponse<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

const apiUrl = process.env.API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000/api/v1";

export async function getFeaturedProducts(): Promise<Product[]> {
  const response = await fetch(`${apiUrl}/products/?featured=true`, {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    throw new Error(`NOVA API returned ${response.status}`);
  }
  const payload = (await response.json()) as PaginatedResponse<Product>;
  return payload.results;
}

export function formatMoney(cents: number, currency = "SAR") {
  return new Intl.NumberFormat("ar-SA", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(cents / 100);
}
