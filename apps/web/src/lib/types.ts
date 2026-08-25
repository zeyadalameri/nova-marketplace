export type Category = {
  id: number;
  name: string;
  slug: string;
  description: string;
  image_url: string;
  display_order: number;
};

export type ProductVariant = {
  id: number;
  name: string;
  sku: string;
  attributes: Record<string, string>;
  price_delta_cents: number;
  price_cents: number;
  display_price_cents: number;
  display_currency: string;
  stock: number;
  is_available: boolean;
};

export type Product = {
  id: number;
  name: string;
  slug: string;
  brand: string;
  sku: string;
  description: string;
  price_cents: number;
  price: string;
  currency: string;
  display_price_cents: number;
  display_currency: string;
  stock: number;
  image_url: string;
  images: { id: number; url: string; alt_text: string }[];
  variants: ProductVariant[];
  has_variants: boolean;
  is_featured: boolean;
  is_available: boolean;
  average_rating: number;
  review_count: number;
  category: Category;
};

export type User = {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  phone: string;
  city: string;
  address: string;
  is_staff: boolean;
};

export type InventoryStockRow = {
  product_id: number;
  variant_id: number | null;
  name: string;
  variant_name: string;
  sku: string;
  category: string;
  stock: number;
  threshold: number;
  reorder_quantity: number;
  sold_units: number;
  revenue_cents: number;
  days_to_stockout: number | null;
  status: "healthy" | "low" | "out";
};

export type InventoryDashboard = {
  period_days: number;
  generated_at: string;
  overview: { products: number; total_stock: number; inventory_value_cents: number; sold_units: number; revenue_cents: number; active_alerts: number; low_stock_items: number; expiring_batches: number };
  stock: InventoryStockRow[];
  top_sellers: InventoryStockRow[];
  slow_movers: InventoryStockRow[];
  movements_by_day: Array<{ day: string; sales: number; incoming: number; adjustments: number }>;
  recent_movements: Array<{ id: number; product: string; variant: string; sku: string; kind: string; quantity_delta: number; stock_after: number; reason: string; created_at: string }>;
  alerts: Array<{ id: number; type: string; severity: string; message: string; acknowledged: boolean; last_seen_at: string }>;
  expiring_batches: Array<{ id: number; product: string; variant: string; lot_number: string; quantity: number; expires_at: string; days_left: number }>;
};

export type InventoryInsight = {
  id: number;
  source: "local" | "openai";
  ai_status: string;
  summary: string;
  priorities: Array<{ title: string; reason: string; action: string; urgency: string }>;
  opportunities: string[];
  risks: string[];
};

export type Address = {
  id: number;
  label: string;
  full_name: string;
  phone: string;
  country_code: string;
  city: string;
  region: string;
  postal_code: string;
  line1: string;
  line2: string;
  is_default: boolean;
};

export type CartItem = {
  id: number;
  product: Product;
  variant: ProductVariant | null;
  quantity: number;
  line_total_cents: number;
};

export type Cart = {
  id: number;
  items: CartItem[];
  item_count: number;
  subtotal_cents: number;
  discount_cents: number;
  tax_cents: number;
  shipping_cents: number;
  total_cents: number;
  currency: string;
  coupon_code: string;
};

export type Payment = {
  public_id: string;
  provider: string;
  status: string;
  amount_cents: number;
  currency: string;
  client_secret?: string;
};

export type Order = {
  public_id: string;
  invoice_number: string;
  status: string;
  payment_status: string;
  payment_method: string;
  full_name: string;
  phone: string;
  city: string;
  address: string;
  notes: string;
  currency: string;
  subtotal_cents: number;
  discount_cents: number;
  tax_cents: number;
  shipping_cents: number;
  total_cents: number;
  items: Array<{
    id: number;
    product_name: string;
    variant_name: string;
    quantity: number;
    price_cents: number;
    line_total_cents: number;
  }>;
  shipment: null | {
    provider: string;
    tracking_number: string;
    tracking_url: string;
    status: string;
    estimated_delivery_at: string | null;
  };
  latest_payment: Payment | null;
  created_at: string;
};

export type Paginated<T> = { count: number; next: string | null; previous: string | null; results: T[] };
