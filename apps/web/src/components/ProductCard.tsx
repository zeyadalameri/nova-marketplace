"use client";

import Link from "next/link";
import { useState } from "react";

import { errorMessage, formatMoney } from "@/lib/client-api";
import type { Product } from "@/lib/types";
import { ProductVisual } from "./ProductVisual";
import { useStore } from "./StoreProvider";

export function ProductCard({ product, compact = false }: { product: Product; compact?: boolean }) {
  const { addToCart, toggleFavorite, favorites, language } = useStore();
  const [message, setMessage] = useState("");
  const image = product.images[0]?.url || product.image_url;
  const price = product.display_price_cents ?? product.price_cents;

  async function act(action: () => Promise<void>, success: string) {
    try { await action(); setMessage(success); } catch (error) { setMessage(errorMessage(error)); }
  }

  return (
    <article className={`product-card${compact ? " product-card-compact" : ""}`}>
      <div className="product-media">
        {product.is_featured && <span className="product-badge">عرض مميز</span>}
        <button className="floating-favorite" aria-label="المفضلة" onClick={() => void act(() => toggleFavorite(product), "تم تحديث المفضلة")}>{favorites.has(product.id) ? "♥" : "♡"}</button>
        <Link href={`/products/${product.slug}`} aria-label={`عرض ${product.name}`}><ProductVisual name={product.name} slug={product.slug} image={image}/></Link>
      </div>
      <div className="product-body">
        <div className="product-meta"><small>{product.category.name} · {product.brand}</small><span>★ {product.average_rating || "جديد"}</span></div>
        <Link href={`/products/${product.slug}`}><h3>{product.name}</h3></Link>
        <p className="product-description">{product.description}</p>
        <div className="product-bottom"><strong>{formatMoney(price, product.display_currency ?? product.currency, language === "ar" ? "ar-SA" : "en-US")}</strong><span className={product.is_available ? "in-stock" : "out-stock"}>{product.is_available ? "متوفر الآن" : "نفد المخزون"}</span></div>
        {product.is_available && <p className="delivery-note">توصيل سريع · استرجاع خلال 14 يومًا</p>}
        <div className="card-actions">
          <button disabled={!product.is_available || product.has_variants} onClick={() => void act(() => addToCart(product), "أضيفت للسلة")}>{product.has_variants ? "اختر المقاس" : "أضف إلى السلة"}</button>
          <Link className="quick-view" href={`/products/${product.slug}`}>التفاصيل</Link>
        </div>
        {message && <p className="inline-message" role="status">{message}</p>}
      </div>
    </article>
  );
}
