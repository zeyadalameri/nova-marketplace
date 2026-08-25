"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { ProductCard } from "@/components/ProductCard";
import { useStore } from "@/components/StoreProvider";
import { apiRequest } from "@/lib/client-api";
import type { Paginated, Product } from "@/lib/types";

export default function FavoritesPage() {
  const { user, favorites } = useStore(); const [products, setProducts] = useState<Product[]>([]);
  useEffect(() => {
    if (!user) return;
    void apiRequest<Paginated<{ id: number; product: Product }> | Array<{ id: number; product: Product }>>("/favorites/").then((payload) => setProducts((Array.isArray(payload) ? payload : payload.results).map((item) => item.product)));
  }, [user, favorites]);
  if (!user) return <main className="page container"><div className="empty-state"><h1>سجّل الدخول أولًا</h1><Link className="primary-button" href="/login">تسجيل الدخول</Link></div></main>;
  return <main className="page container"><div className="page-heading"><p className="eyebrow">قائمتك الخاصة</p><h1>المفضلة</h1></div>{products.length ? <div className="product-grid">{products.map((product) => <ProductCard product={product} key={product.id}/>)}</div> : <div className="empty-state"><h2>المفضلة فارغة</h2><p>اضغط رمز القلب بجانب المنتجات التي تعجبك.</p><Link className="primary-button" href="/">استكشف المنتجات</Link></div>}</main>;
}
